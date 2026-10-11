from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def _validate_password_strength(value: str) -> str:
    if not any(char.isdigit() for char in value):
        raise ValueError("Password must contain at least one number")

    if not any(not char.isalnum() for char in value):
        raise ValueError("Password must contain at least one special character")

    return value


class SignupRequest(BaseModel):

    username: str = Field(..., min_length=3, max_length=30)

    email: EmailStr = Field(..., max_length=255)

    create_password: str = Field(..., min_length=8, max_length=128)

    confirm_password: str = Field(..., max_length=128)

    verification_method: Literal["link", "otp"] = "link"

    @field_validator("create_password")
    @classmethod
    def validate_password(cls, value):
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.create_password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self


class SignupResponse(BaseModel):
    success: bool
    message: str


class LoginRequest(BaseModel):
    identifier: str = Field(..., max_length=255, description="Email address or username")
    password: str = Field(..., max_length=128)


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    username: str
    email: str
    email_verified: bool


class LogoutResponse(BaseModel):
    success: bool
    message: str


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., max_length=128, description="Current password, required to confirm deletion")


class DeleteAccountResponse(BaseModel):
    success: bool
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    method: Literal["link", "otp"] = "link"


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., max_length=512)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self


class GenericMessageResponse(BaseModel):
    success: bool
    message: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., max_length=512)


class VerifyEmailResponse(BaseModel):
    success: bool
    message: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    method: Literal["link", "otp"] = "link"


class CheckUsernameResponse(BaseModel):
    available: bool
    # Omitted entirely (via response_model_exclude_none on the route)
    # when the username is available — matches the API contract's
    # `{ "available": true }` shape exactly, with no empty/null key.
    suggestions: list[str] | None = None


class VerifyEmailOtpRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    otp_code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordOtpRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self