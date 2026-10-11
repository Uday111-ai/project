import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import database
from app.core import config
from app.core.audit import log_event
from app.core.email import (
    send_reset_email,
    send_reset_otp_email,
    send_verification_email,
    send_verification_otp_email,
)
from app.core.jwt import create_access_token, verify_access_token
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    generate_otp_code,
    generate_reset_token,
    hash_password,
    is_password_pwned,
    verify_password,
)
from app.core.username_suggestions import generate_candidates
from app.database import Base, SessionLocal, engine
from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.user import (
    CheckUsernameResponse,
    DeleteAccountRequest,
    DeleteAccountResponse,
    ForgotPasswordRequest,
    GenericMessageResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    ResendVerificationRequest,
    ResetPasswordOtpRequest,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    VerifyEmailOtpRequest,
    VerifyEmailRequest,
    VerifyEmailResponse,
)

load_dotenv()

logger = logging.getLogger("uvicorn.error")

if config.DB_AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

app = FastAPI()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=config.RATE_LIMIT_STORAGE_URI,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_default_origins = os.getenv("FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains"
    )
    return response


security = HTTPBearer()


@app.get("/")
def home():
    return {'message': 'Welcome to the AI Auth Demo API!'}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


ACCOUNT_LOCKED_MESSAGE = (
    "This account is temporarily locked due to repeated failed login "
    "attempts. Please try again later."
)


@app.get(
    "/check-username",
    response_model=CheckUsernameResponse,
    response_model_exclude_none=True,
)
@limiter.limit("30/minute")
def check_username(
    request: Request,
    username: str = Query(..., min_length=3, max_length=30),
    db: Session = Depends(get_db),
):
    username_lower = username.lower()

    existing = db.query(User).filter(
        func.lower(User.username) == username_lower
    ).first()

    if not existing:
        return {"available": True}

    candidates = generate_candidates(username)
    suggestions: list[str] = []
    if candidates:
        taken_lower = {
            row.username.lower()
            for row in db.query(User.username)
            .filter(func.lower(User.username).in_([c.lower() for c in candidates]))
            .all()
        }
        suggestions = [c for c in candidates if c.lower() not in taken_lower][:4]

    return {"available": False, "suggestions": suggestions}


@app.post("/signup", response_model=SignupResponse, status_code=201)
@limiter.limit("5/hour")
def signup(
    request: Request,
    background_tasks: BackgroundTasks,
    user: SignupRequest,
    db: Session = Depends(get_db),
):
    username_lower = user.username.lower()
    email_lower = str(user.email).lower()

    existing = db.query(User).filter(
        or_(
            func.lower(User.username) == username_lower,
            func.lower(User.email) == email_lower,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this username or email already exists",
        )

    if config.CHECK_PASSWORD_PWNED:
        try:
            if is_password_pwned(user.create_password):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This password has appeared in known data breaches. "
                        "Please choose a different password."
                    ),
                )
        except HTTPException:
            raise
        except Exception:
            logger.exception("Pwned-password check failed; continuing without it")

    hashed_password = hash_password(user.create_password)

    new_user = User(
        username=user.username,
        email=str(user.email),
        password_hash=hashed_password,
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this username or email already exists",
        )
    db.refresh(new_user)

    verification_token = generate_reset_token()
    verification_record = EmailVerificationToken(
        user_id=new_user.id,
        token_hash=_hash_token(verification_token),
        expires_at=_now()
        + timedelta(minutes=config.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES),
    )

    if user.verification_method == "otp":
        otp_code = generate_otp_code()
        verification_record.delivery_method = "otp"
        verification_record.otp_hash = _hash_token(otp_code)
        db.add(verification_record)
        db.commit()
        background_tasks.add_task(
            send_verification_otp_email, str(user.email), otp_code
        )
    else:
        db.add(verification_record)
        db.commit()
        verify_link = (
            f"{config.FRONTEND_URL}/verify-email?token={verification_token}"
        )
        background_tasks.add_task(
            send_verification_email, str(user.email), verify_link
        )

    log_event("signup", user_id=new_user.id, delivery_method=user.verification_method)

    message = "Account created successfully."
    if config.REQUIRE_EMAIL_VERIFICATION:
        message += " Please check your email to verify your account before logging in."

    return {"success": True, "message": message}


@app.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(request: Request, user: LoginRequest, db: Session = Depends(get_db)):
    identifier_lower = user.identifier.lower()

    existing_user = db.query(User).filter(
        or_(
            func.lower(User.email) == identifier_lower,
            func.lower(User.username) == identifier_lower,
        )
    ).first()

    password_hash_to_check = (
        existing_user.password_hash if existing_user else DUMMY_PASSWORD_HASH
    )
    password_valid = verify_password(user.password, password_hash_to_check)

    if not existing_user:
        log_event("login_failed", reason="no_such_user")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    now = _now()
    if existing_user.locked_until is not None and existing_user.locked_until > now:
        log_event("login_blocked_locked", user_id=existing_user.id)
        raise HTTPException(status_code=423, detail=ACCOUNT_LOCKED_MESSAGE)

    if not password_valid:
        existing_user.failed_login_attempts += 1
        if existing_user.failed_login_attempts >= config.ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
            existing_user.locked_until = now + timedelta(
                minutes=config.ACCOUNT_LOCKOUT_DURATION_MINUTES
            )
            existing_user.failed_login_attempts = 0
            log_event("account_locked", user_id=existing_user.id)
        db.commit()
        log_event("login_failed", user_id=existing_user.id, reason="bad_password")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if config.REQUIRE_EMAIL_VERIFICATION and not existing_user.email_verified:
        log_event("login_blocked_unverified", user_id=existing_user.id)
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address before logging in.",
        )

    existing_user.failed_login_attempts = 0
    existing_user.locked_until = None
    db.commit()

    access_token = create_access_token(
        existing_user.id,
        existing_user.token_version,
    )

    log_event("login_success", user_id=existing_user.id)

    return {
        "success": True,
        "message": "Login successful",
        "access_token": access_token,
    }


def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    token_data = verify_access_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id, token_version = token_data

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if user.token_version != token_version:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user


@app.get("/me", response_model=MeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
    }


@app.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.token_version += 1
    db.commit()

    log_event("logout", user_id=current_user.id)

    return {
        "success": True,
        "message": "Logged out successfully"
    }


@app.post("/delete-account", response_model=DeleteAccountResponse)
def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password"
        )

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == current_user.id
    ).delete()
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id
    ).delete()

    user_id = current_user.id
    db.delete(current_user)
    db.commit()

    log_event("account_deleted", user_id=user_id)

    return {
        "success": True,
        "message": "Account deleted successfully"
    }


@app.post("/forgot-password", response_model=GenericMessageResponse)
@limiter.limit("5/hour")
def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    request_body: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    email_lower = str(request_body.email).lower()

    user = db.query(User).filter(func.lower(User.email) == email_lower).first()

    generic_message = {
        "success": True,
        "message": "If an account exists with this email, a password reset link has been sent.",
    }

    if not user:
        _hash_token(secrets.token_urlsafe(32))
        log_event("forgot_password_requested", found=False)
        return generic_message

    reset_token = generate_reset_token()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(reset_token),
        expires_at=_now()
        + timedelta(minutes=config.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )

    if request_body.method == "otp":
        otp_code = generate_otp_code()
        reset_record.delivery_method = "otp"
        reset_record.otp_hash = _hash_token(otp_code)
        db.add(reset_record)
        db.commit()
        background_tasks.add_task(
            send_reset_otp_email, str(request_body.email), otp_code
        )
    else:
        db.add(reset_record)
        db.commit()
        reset_link = f"{config.FRONTEND_URL}/reset-password?token={reset_token}"
        background_tasks.add_task(
            send_reset_email, str(request_body.email), reset_link
        )

    log_event("forgot_password_requested", found=True, user_id=user.id)

    return generic_message


@app.post("/reset-password", response_model=GenericMessageResponse)
@limiter.limit("10/hour")
def reset_password(
    request: Request,
    request_body: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    token_hash = _hash_token(request_body.token)

    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used == False  # noqa: E712
    ).first()

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    if reset_record.expires_at < _now():
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    user = db.query(User).filter(
        User.id == reset_record.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    user.password_hash = hash_password(request_body.new_password)
    user.token_version += 1
    user.failed_login_attempts = 0
    user.locked_until = None

    reset_record.used = True

    db.commit()

    log_event("password_reset", user_id=user.id)

    return {
        "success": True,
        "message": "Password reset successfully"
    }


@app.post("/verify-email", response_model=VerifyEmailResponse)
def verify_email(request_body: VerifyEmailRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(request_body.token)

    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.used == False,  # noqa: E712
    ).first()

    if not record or record.expires_at < _now():
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link",
        )

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link",
        )

    user.email_verified = True
    record.used = True
    db.commit()

    log_event("email_verified", user_id=user.id)

    return {"success": True, "message": "Email verified successfully. You can now log in."}


@app.post("/resend-verification-email", response_model=GenericMessageResponse)
@limiter.limit("5/hour")
def resend_verification_email(
    request: Request,
    background_tasks: BackgroundTasks,
    request_body: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    email_lower = str(request_body.email).lower()
    user = db.query(User).filter(func.lower(User.email) == email_lower).first()

    generic_message = {
        "success": True,
        "message": (
            "If an account exists with this email and is not yet verified, "
            "a new verification code has been sent."
        ),
    }

    if not user or user.email_verified:
        _hash_token(secrets.token_urlsafe(32))
        return generic_message

    verification_token = generate_reset_token()
    verification_record = EmailVerificationToken(
        user_id=user.id,
        token_hash=_hash_token(verification_token),
        expires_at=_now()
        + timedelta(minutes=config.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES),
    )

    if request_body.method == "otp":
        otp_code = generate_otp_code()
        verification_record.delivery_method = "otp"
        verification_record.otp_hash = _hash_token(otp_code)
        db.add(verification_record)
        db.commit()
        background_tasks.add_task(
            send_verification_otp_email, str(user.email), otp_code
        )
    else:
        db.add(verification_record)
        db.commit()
        verify_link = (
            f"{config.FRONTEND_URL}/verify-email?token={verification_token}"
        )
        background_tasks.add_task(
            send_verification_email, str(user.email), verify_link
        )

    log_event("verification_email_resent", user_id=user.id, delivery_method=request_body.method)

    return generic_message


@app.post("/verify-email/otp", response_model=VerifyEmailResponse)
@limiter.limit("5/minute")
def verify_email_otp(
    request: Request,
    request_body: VerifyEmailOtpRequest,
    db: Session = Depends(get_db),
):
    email_lower = str(request_body.email).lower()
    user = db.query(User).filter(func.lower(User.email) == email_lower).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.delivery_method == "otp",
        EmailVerificationToken.otp_hash == _hash_token(request_body.otp_code),
        EmailVerificationToken.used == False,  # noqa: E712
    ).first()

    if not record or record.expires_at < _now():
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    user.email_verified = True
    record.used = True
    db.commit()

    log_event("email_verified", user_id=user.id, delivery_method="otp")

    return {"success": True, "message": "Email verified successfully. You can now log in."}


@app.post("/reset-password/otp", response_model=GenericMessageResponse)
@limiter.limit("5/minute")
def reset_password_otp(
    request: Request,
    request_body: ResetPasswordOtpRequest,
    db: Session = Depends(get_db),
):
    email_lower = str(request_body.email).lower()
    user = db.query(User).filter(func.lower(User.email) == email_lower).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.delivery_method == "otp",
        PasswordResetToken.otp_hash == _hash_token(request_body.otp_code),
        PasswordResetToken.used == False,  # noqa: E712
    ).first()

    if not record or record.expires_at < _now():
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    user.password_hash = hash_password(request_body.new_password)
    user.token_version += 1
    user.failed_login_attempts = 0
    user.locked_until = None

    record.used = True

    db.commit()

    log_event("password_reset", user_id=user.id, delivery_method="otp")

    return {"success": True, "message": "Password reset successfully"}