import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import UserRole
from app.infrastructure.database.models.driver_model import DriverModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.vehicle_model import VehicleModel
from app.schemas.responses.auth_responses import UserResponse
from app.schemas.responses.driver_responses import DriverResponse, VehicleResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: UserModel = Depends(require_roles(UserRole.ADMIN))) -> list[UserResponse]:
    users = db.scalars(select(UserModel).where(UserModel.deleted_at.is_(None)).order_by(UserModel.created_at.desc())).all()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/drivers", response_model=list[DriverResponse])
def list_drivers(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.ADMIN)),
) -> list[DriverResponse]:
    drivers = db.scalars(
        select(DriverModel)
        .where(DriverModel.deleted_at.is_(None))
        .order_by(DriverModel.created_at.desc())
    ).all()
    return [DriverResponse.model_validate(driver) for driver in drivers]


@router.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.ADMIN)),
) -> list[VehicleResponse]:
    vehicles = db.scalars(
        select(VehicleModel)
        .where(VehicleModel.deleted_at.is_(None))
        .order_by(VehicleModel.created_at.desc())
    ).all()
    return [VehicleResponse.model_validate(vehicle) for vehicle in vehicles]


@router.post("/drivers/{driver_id}/approve", response_model=DriverResponse)
def approve_driver(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.ADMIN)),
) -> DriverResponse:
    driver = db.get(DriverModel, driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    driver.approval_status = "approved"
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.post("/vehicles/{vehicle_id}/approve", response_model=VehicleResponse)
def approve_vehicle(
    vehicle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.ADMIN)),
) -> VehicleResponse:
    vehicle = db.get(VehicleModel, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    vehicle.approval_status = "approved"
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)
