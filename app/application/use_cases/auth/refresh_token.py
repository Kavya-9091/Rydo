from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import UserRole, UserStatus
from app.infrastructure.database.models.refresh_token_model import RefreshTokenModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.services.jwt_service import jwt_service


class InvalidRefreshTokenError(Exception):
    pass


class RefreshTokenUseCase:
    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, refresh_token: str) -> tuple[UserModel, str, str]:
        token_hash = jwt_service.hash_refresh_token(refresh_token)
        stored_token = self._db.scalar(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )

        now = datetime.now(UTC)
        if not stored_token or stored_token.expires_at <= now:
            raise InvalidRefreshTokenError("Refresh token is invalid or expired")

        user = self._db.get(UserModel, stored_token.user_id)
        if not user or user.deleted_at is not None or user.status != UserStatus.ACTIVE.value:
            raise InvalidRefreshTokenError("Refresh token is invalid or expired")

        access_token = jwt_service.create_access_token(user_id=user.id, role=UserRole(user.role))
        new_refresh_token, new_token_hash, expires_at = jwt_service.create_refresh_token()

        stored_token.revoked_at = now
        stored_token.replaced_by_token_hash = new_token_hash
        self._db.add(
            RefreshTokenModel(
                user_id=user.id,
                token_hash=new_token_hash,
                expires_at=expires_at,
            )
        )
        self._db.commit()
        self._db.refresh(user)
        return user, access_token, new_refresh_token
