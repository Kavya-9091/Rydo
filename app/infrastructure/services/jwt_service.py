import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.security import TokenType, UserRole
from app.core.settings import get_settings


class TokenError(Exception):
    pass


class JwtService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def create_access_token(self, *, user_id: uuid.UUID, role: UserRole) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "role": role.value,
            "type": TokenType.ACCESS.value,
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.access_token_expire_minutes),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm)

    def create_refresh_token(self) -> tuple[str, str, datetime]:
        token = secrets.token_urlsafe(64)
        token_hash = self.hash_refresh_token(token)
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)
        return token, token_hash, expires_at

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
        except InvalidTokenError as exc:
            raise TokenError("Invalid access token") from exc

        if payload.get("type") != TokenType.ACCESS.value:
            raise TokenError("Invalid token type")
        return payload

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


jwt_service = JwtService()
