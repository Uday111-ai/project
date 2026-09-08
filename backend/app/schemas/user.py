from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class SignupRequest(BaseModel):

    username: str = Field(..., min_length=3, max_length=30)

    email: EmailStr = Field(..., )

    create_password: str = Field(..., min_length=8)

    confirm_password: str = Field(..., )

    @field_validator("create_password")
    @classmethod
    def validate_password(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")

        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must contain at least one special character")

        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.create_password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self

class SignupResponse(BaseModel):
    success: bool
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")

        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must contain at least one special character")

        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self