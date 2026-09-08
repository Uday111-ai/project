import logging
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.user import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    LogoutResponse,
    DeleteAccountRequest,
    DeleteAccountResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.core.security import hash_password, verify_password, generate_reset_token
from app.core.jwt import create_access_token, verify_access_token
from app.core.email import send_reset_email
from app import database
from app.models.user import User
from app.database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from app.models.password_reset_token import PasswordResetToken
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("uvicorn.error")

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS: comma-separated list of allowed frontend origins, e.g.
#   CORS_ORIGINS=http://localhost:3000,https://your-frontend.netlify.app
# Falls back to FRONTEND_URL, then localhost:3000 for local dev.
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

@app.post("/signup", response_model=SignupResponse, status_code=201)
def signup(user: SignupRequest, db: Session = Depends(get_db)):

    existing_username = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already taken"
        )

    existing_email = db.query(User).filter(
        User.email == str(user.email)
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email ID already registered"
        )

    hashed_password = hash_password(user.create_password)

    new_user = User(
        username=user.username,
        email=str(user.email),
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()

    return {
        "success": True,
        "message": "Account created successfully"
    }

@app.post("/login", response_model=LoginResponse)
def login(user: LoginRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.email == str(user.email)
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        user.password,
        existing_user.password_hash
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        existing_user.id,
        existing_user.token_version
    )

    return {
        "success": True,
        "message": "Login successful",
        "access_token": access_token
    }


def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Shared auth dependency: validates the bearer token and returns the
    current User row. Used by /me, /logout, and /delete-account."""
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
        "email": current_user.email
    }


@app.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Stateless JWTs can't be revoked directly, so logout bumps
    # token_version (the same mechanism used on password reset). This
    # invalidates every access token currently issued to this user,
    # which is the simplest correct behavior for a single-session demo.
    current_user.token_version += 1
    db.commit()

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

    # Clear out any password-reset tokens for this user first, since
    # they reference users.id via a foreign key.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == current_user.id
    ).delete()

    db.delete(current_user)
    db.commit()

    return {
        "success": True,
        "message": "Account deleted successfully"
    }

@app.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == str(request.email)
    ).first()

    if not user:
        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    reset_token = generate_reset_token()

    token_hash = sha256(reset_token.encode()).hexdigest()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
    )

    db.add(reset_record)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL")

    reset_link = f"{frontend_url}/reset-password?token={reset_token}"  

    try:
        send_reset_email(
            str(request.email),
            reset_link
        )
    except Exception:
        # Don't let an SMTP/network hiccup surface details to the caller
        # (and don't reveal whether the account exists via an error).
        logger.exception("Failed to send password reset email")

    return {
        "success": True,
        "message": "If an account exists with this email, a password reset link has been sent."
    }

@app.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    token_hash = sha256(request.token.encode()).hexdigest()

    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used == False
    ).first()

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    if reset_record.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
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

    user.password_hash = hash_password(request.new_password)

    user.token_version += 1

    reset_record.used = True

    db.commit()

    return {
        "success": True,
        "message": "Password reset successfully"
    }