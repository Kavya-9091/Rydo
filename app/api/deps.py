from collections.abc import Callable
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import UserRole, UserStatus
from app.database import get_db_session
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.services.jwt_service import TokenError, jwt_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_db(db: Session = Depends(get_db_session)) -> Session:
    return db


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_service.decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, TokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(UserModel, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    return user


def require_roles(*roles: UserRole) -> Callable[[UserModel], UserModel]:
    allowed_roles = {role.value for role in roles}

    def dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency
