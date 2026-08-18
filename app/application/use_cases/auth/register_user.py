from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import UserStatus
from app.infrastructure.database.models.refresh_token_model import RefreshTokenModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.services.jwt_service import jwt_service
from app.infrastructure.services.password_service import password_service
from app.schemas.requests.auth_requests import RegisterRequest


class UserAlreadyExistsError(Exception):
    pass


class RegisterUserUseCase:
    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, request: RegisterRequest) -> tuple[UserModel, str, str]:
        existing_user = self._db.scalar(
            select(UserModel).where(
                UserModel.deleted_at.is_(None),
                or_(
                    UserModel.email == request.email.lower(),
                    UserModel.phone_number == request.phone_number,
                ),
            )
        )
        if existing_user:
            raise UserAlreadyExistsError("A user with this email or phone number already exists")

        user = UserModel(
            email=request.email.lower(),
            phone_number=request.phone_number,
            password_hash=password_service.hash_password(request.password),
            full_name=request.full_name,
            role=request.role.value,
            status=UserStatus.ACTIVE.value,
        )
        self._db.add(user)
        self._db.flush()

        access_token = jwt_service.create_access_token(user_id=user.id, role=request.role)
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
