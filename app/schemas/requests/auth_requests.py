from pydantic import BaseModel, EmailStr, Field

from app.core.security import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=32)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=32)
