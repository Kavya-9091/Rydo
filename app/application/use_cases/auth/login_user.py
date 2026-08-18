from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import UserRole, UserStatus
from app.infrastructure.database.models.refresh_token_model import RefreshTokenModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.services.jwt_service import jwt_service
from app.infrastructure.services.password_service import password_service
from app.schemas.requests.auth_requests import LoginRequest


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class LoginUserUseCase:
    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, request: LoginRequest) -> tuple[UserModel, str, str]:
        user = self._db.scalar(
            select(UserModel).where(
                UserModel.email == request.email.lower(),
                UserModel.deleted_at.is_(None),
            )
        )
        if not user or not password_service.verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if user.status != UserStatus.ACTIVE.value:
            raise InactiveUserError("User is not active")

        user.last_login_at = datetime.now(UTC)
        role = UserRole(user.role)
        access_token = jwt_service.create_access_token(user_id=user.id, role=role)
        refresh_token, refresh_token_hash, expires_at = jwt_service.create_refresh_token()
        self._db.add(
            RefreshTokenModel(
                user_id=user.id,
                token_hash=refresh_token_hash,
                expires_at=expires_at,
            )
        )
        self._db.commit()
        self._db.refresh(user)
        return user, access_token, refresh_token
