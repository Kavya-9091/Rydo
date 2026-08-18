from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.application.use_cases.auth.login_user import (
    InactiveUserError,
    InvalidCredentialsError,
    LoginUserUseCase,
)
from app.application.use_cases.auth.logout_user import LogoutUserUseCase
from app.application.use_cases.auth.refresh_token import InvalidRefreshTokenError, RefreshTokenUseCase
from app.application.use_cases.auth.register_user import RegisterUserUseCase, UserAlreadyExistsError
from app.infrastructure.database.models.user_model import UserModel
from app.schemas.requests.auth_requests import LoginRequest, RefreshTokenRequest, RegisterRequest
from app.schemas.responses.auth_responses import AuthResponse, TokenPairResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, access_token, refresh_token = RegisterUserUseCase(db).execute(request)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenPairResponse(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, access_token, refresh_token = LoginUserUseCase(db).execute(request)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except InactiveUserError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenPairResponse(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, access_token, new_refresh_token = RefreshTokenUseCase(db).execute(request.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenPairResponse(access_token=access_token, refresh_token=new_refresh_token),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> Response:
    LogoutUserUseCase(db).execute(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(current_user: UserModel = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
