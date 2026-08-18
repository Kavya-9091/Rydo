from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models.refresh_token_model import RefreshTokenModel
from app.infrastructure.services.jwt_service import jwt_service


class LogoutUserUseCase:
    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, refresh_token: str) -> None:
        token_hash = jwt_service.hash_refresh_token(refresh_token)
        stored_token = self._db.scalar(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        if stored_token:
            stored_token.revoked_at = datetime.now(UTC)
            self._db.commit()
