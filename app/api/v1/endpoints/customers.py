from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import UserRole
from app.infrastructure.database.models.payment_model import PaymentModel
from app.infrastructure.database.models.ride_model import RideModel
from app.infrastructure.database.models.user_model import UserModel
from app.schemas.responses.auth_responses import UserResponse
from app.schemas.responses.ride_responses import PaymentResponse, RideResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/me", response_model=UserResponse)
def get_customer_profile(current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER))) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/rides", response_model=list[RideResponse])
def get_ride_history(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER)),
) -> list[RideResponse]:
    rides = db.scalars(
        select(RideModel)
        .where(RideModel.customer_id == current_user.id, RideModel.deleted_at.is_(None))
        .order_by(RideModel.requested_at.desc())
    ).all()
    return [RideResponse.model_validate(ride) for ride in rides]


@router.get("/payments", response_model=list[PaymentResponse])
def get_payment_history(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER)),
) -> list[PaymentResponse]:
    payments = db.scalars(
        select(PaymentModel)
        .where(PaymentModel.payer_user_id == current_user.id, PaymentModel.deleted_at.is_(None))
        .order_by(PaymentModel.created_at.desc())
    ).all()
    return [PaymentResponse.model_validate(payment) for payment in payments]
