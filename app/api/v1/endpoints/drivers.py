from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import UserRole
from app.infrastructure.database.models.driver_model import DriverModel
from app.infrastructure.database.models.ride_model import RideModel
from app.infrastructure.database.models.ride_rejection_model import RideRejectionModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.vehicle_model import VehicleModel
from app.schemas.requests.driver_requests import DriverAvailabilityRequest, VehicleCreateRequest
from app.schemas.responses.driver_responses import DriverResponse, VehicleResponse
from app.schemas.responses.ride_responses import RideResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("/me", response_model=DriverResponse)
def get_driver_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> DriverResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")
    return DriverResponse.model_validate(driver)


@router.post("/register", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def register_driver(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> DriverResponse:
    existing = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if existing:
        return DriverResponse.model_validate(existing)
    driver = DriverModel(user_id=current_user.id)
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def register_vehicle(
    request: VehicleCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> VehicleResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver profile is required")
    payload = request.model_dump()
    payload["registration_number"] = payload["registration_number"].strip().upper()
    existing_vehicle = db.scalar(
        select(VehicleModel).where(
            VehicleModel.registration_number == payload["registration_number"],
            VehicleModel.deleted_at.is_(None),
        )
    )
    if existing_vehicle:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle registration number already exists")
    vehicle = VehicleModel(driver_id=driver.id, **payload)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.post("/online", response_model=DriverResponse)
def go_online(
    request: DriverAvailabilityRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> DriverResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver profile is required")
    if driver.approval_status != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver is not approved")
    driver.availability_status = "online"
    driver.current_latitude = request.latitude
    driver.current_longitude = request.longitude
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.post("/offline", response_model=DriverResponse)
def go_offline(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> DriverResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver profile is required")
    driver.availability_status = "offline"
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.get("/rides", response_model=list[RideResponse])
def list_assigned_rides(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> list[RideResponse]:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    vehicle_types = db.scalars(
        select(VehicleModel.vehicle_type).where(
            VehicleModel.driver_id == driver.id,
            VehicleModel.deleted_at.is_(None),
            VehicleModel.is_active.is_(True),
            VehicleModel.approval_status == "approved",
        )
    ).all()
    if not vehicle_types:
        return []

    rejected_ride_ids = select(RideRejectionModel.ride_id).where(
        RideRejectionModel.driver_id == driver.id,
        RideRejectionModel.deleted_at.is_(None),
    )
    rides = db.scalars(
        select(RideModel)
        .where(
            RideModel.deleted_at.is_(None),
            RideModel.id.not_in(rejected_ride_ids),
            RideModel.status.in_(["requested", "accepted", "in_progress"]),
            or_(
                RideModel.driver_id == driver.id,
                (
                    RideModel.driver_id.is_(None)
                    & (RideModel.status == "requested")
                    & RideModel.ride_type.in_(vehicle_types)
                ),
            ),
        )
        .order_by(RideModel.requested_at.desc())
    ).all()
    return [RideResponse.model_validate(ride) for ride in rides]
