import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.security import UserRole, UserStatus


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    phone_number: str
    full_name: str
    role: UserRole
    status: UserStatus


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPairResponse
