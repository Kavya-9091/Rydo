from datetime import UTC, datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import UserRole
from app.infrastructure.database.models.driver_model import DriverModel
from app.infrastructure.database.models.payment_model import PaymentModel
from app.infrastructure.database.models.rating_model import RatingModel
from app.infrastructure.database.models.ride_model import RideModel
from app.infrastructure.database.models.ride_rejection_model import RideRejectionModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.vehicle_model import VehicleModel
from app.infrastructure.services.notification_service import NotificationService
from app.schemas.requests.ride_requests import CancelRideRequest, PaymentCreateRequest, RatingCreateRequest, RideCreateRequest, RideRatingCreateRequest
from app.schemas.responses.driver_responses import NearbyVehicleResponse
from app.schemas.responses.ride_responses import PaymentResponse, RatingResponse, RideDriverDetailsResponse, RideResponse, RideVehicleDetailsResponse
from app.services.fare_calculation_service import FareCalculationService
from app.services.ride_matching_service import RideMatchingService

router = APIRouter(prefix="/rides", tags=["Rides"])


@router.get("/nearby-vehicles", response_model=list[NearbyVehicleResponse])
def get_nearby_vehicles(
    pickup_latitude: float,
    pickup_longitude: float,
    ride_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER)),
) -> list[NearbyVehicleResponse]:
    if not -90 <= pickup_latitude <= 90 or not -180 <= pickup_longitude <= 180:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid pickup coordinates")
    if ride_type and ride_type not in {"bike", "auto", "mini", "sedan", "suv", "luxury"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid vehicle type")

    vehicles = RideMatchingService(db).find_nearby_vehicles(
        pickup_latitude=pickup_latitude,
        pickup_longitude=pickup_longitude,
        ride_type=ride_type,
    )
    return [NearbyVehicleResponse(**vehicle) for vehicle in vehicles]


@router.post("", response_model=RideResponse, status_code=status.HTTP_201_CREATED)
def book_ride(
    request: RideCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER)),
) -> RideResponse:
    fare_service = FareCalculationService()
    distance = fare_service.distance_km(request.pickup_latitude, request.pickup_longitude, request.dropoff_latitude, request.dropoff_longitude)
    estimated_fare = fare_service.estimate_fare(request.ride_type, distance)
    match = RideMatchingService(db).find_nearest_driver(request.ride_type, request.pickup_latitude, request.pickup_longitude)
    ride = RideModel(
        customer_id=current_user.id,
        driver_id=None,
        vehicle_id=None,
        status="requested",
        estimated_distance_km=distance,
        estimated_fare=estimated_fare,
        **request.model_dump(),
    )
    db.add(ride)
    notifier = NotificationService(db)
    notifier.send(
        user_id=current_user.id,
        title="Ride requested",
        message="We are finding a driver for your trip.",
        notification_type="ride_requested",
    )
    if match:
        notifier.send(
            user_id=match[0].user_id,
            title="New ride request",
            message=f"Pickup: {request.pickup_address}",
            notification_type="ride_requested",
        )
    db.commit()
    db.refresh(ride)
    return _ride_response(db, ride)


@router.get("/{ride_id}", response_model=RideResponse)
def get_ride(
    ride_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER, UserRole.DRIVER, UserRole.ADMIN)),
) -> RideResponse:
    ride = db.get(RideModel, ride_id)
    if not ride or ride.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    return _ride_response(db, ride)


@router.post("/{ride_id}/cancel", response_model=RideResponse)
def cancel_ride(
    ride_id: uuid.UUID,
    request: CancelRideRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER, UserRole.DRIVER, UserRole.ADMIN)),
) -> RideResponse:
    ride = db.get(RideModel, ride_id)
    if not ride or ride.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.status in {"completed", "cancelled"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride cannot be cancelled")
    ride.status = "cancelled"
    ride.cancelled_at = datetime.now(UTC)
    ride.cancellation_reason = request.reason
    if ride.driver_id:
        driver = db.get(DriverModel, ride.driver_id)
        if driver:
            driver.availability_status = "online"
            NotificationService(db).send(
                user_id=driver.user_id,
                title="Ride cancelled",
                message=request.reason,
                notification_type="ride_cancelled",
            )
    NotificationService(db).send(
        user_id=ride.customer_id,
        title="Ride cancelled",
        message=request.reason,
        notification_type="ride_cancelled",
    )
    db.commit()
    db.refresh(ride)
    return _ride_response(db, ride)


@router.post("/{ride_id}/accept", response_model=RideResponse)
def accept_ride(ride_id: uuid.UUID, db: Session = Depends(get_db), current_user: UserModel = Depends(require_roles(UserRole.DRIVER))) -> RideResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    ride = db.get(RideModel, ride_id)
    if not ride or ride.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.driver_id and ride.driver_id != driver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ride is assigned to another driver")
    if ride.status != "requested":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride is not waiting for acceptance")

    vehicle = db.scalar(
        select(VehicleModel).where(
            VehicleModel.driver_id == driver.id,
            VehicleModel.deleted_at.is_(None),
            VehicleModel.is_active.is_(True),
            VehicleModel.approval_status == "approved",
            VehicleModel.vehicle_type == ride.ride_type,
        )
    )
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No approved matching vehicle found")

    ride.driver_id = driver.id
    ride.vehicle_id = vehicle.id
    ride.status = "accepted"
    ride.accepted_at = datetime.now(UTC)
    driver.availability_status = "busy"
    NotificationService(db).send(
        user_id=ride.customer_id,
        title="Driver accepted",
        message=_accepted_driver_message(db, driver, vehicle),
        notification_type="ride_accepted",
    )
    db.commit()
    db.refresh(ride)
    return _ride_response(db, ride)


@router.post("/{ride_id}/reject", response_model=RideResponse)
def reject_ride(
    ride_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.DRIVER)),
) -> RideResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    ride = db.get(RideModel, ride_id)
    if not ride or ride.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.status not in {"requested", "accepted"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride cannot be rejected now")

    if ride.driver_id is None and ride.status == "requested":
        existing_rejection = db.scalar(
            select(RideRejectionModel).where(
                RideRejectionModel.ride_id == ride.id,
                RideRejectionModel.driver_id == driver.id,
                RideRejectionModel.deleted_at.is_(None),
            )
        )
        if not existing_rejection:
            db.add(RideRejectionModel(ride_id=ride.id, driver_id=driver.id))
        db.commit()
        db.refresh(ride)
        return _ride_response(db, ride)

    if ride.driver_id != driver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ride is assigned to another driver")

    ride.driver_id = None
    ride.vehicle_id = None
    ride.status = "requested"
    ride.accepted_at = None
    driver.availability_status = "online"
    NotificationService(db).send(
        user_id=ride.customer_id,
        title="Driver unavailable",
        message="Your driver could not continue. We are looking for another driver.",
        notification_type="ride_rejected",
    )
    db.commit()
    db.refresh(ride)
    return _ride_response(db, ride)


@router.post("/{ride_id}/start", response_model=RideResponse)
def start_ride(ride_id: uuid.UUID, db: Session = Depends(get_db), current_user: UserModel = Depends(require_roles(UserRole.DRIVER))) -> RideResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    ride = db.get(RideModel, ride_id)
    if ride and ride.driver_id != driver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ride is assigned to another driver")
    if not ride or ride.status != "accepted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride is not ready to start")
    ride.status = "in_progress"
    ride.started_at = datetime.now(UTC)
    NotificationService(db).send(
        user_id=ride.customer_id,
        title="Ride started",
        message="Your ride is now in progress.",
        notification_type="ride_started",
    )
    db.commit()
    db.refresh(ride)
    return _ride_response(db, ride)


@router.post("/{ride_id}/complete", response_model=RideResponse)
def complete_ride(ride_id: uuid.UUID, db: Session = Depends(get_db), current_user: UserModel = Depends(require_roles(UserRole.DRIVER))) -> RideResponse:
    driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    ride = db.get(RideModel, ride_id)
    if ride and ride.driver_id != driver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ride is assigned to another driver")
    if not ride or ride.status != "in_progress":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride is not in progress")
    ride.status = "completed"
    ride.completed_at = datetime.now(UTC)
    ride.final_fare = ride.estimated_fare
    if ride.driver_id:
        driver = db.get(DriverModel, ride.driver_id)
        if driver:
            driver.availability_status = "online"
            driver.total_rides += 1
    NotificationService(db).send(
        user_id=ride.customer_id,
        title="Ride completed",
        message="Your ride is complete. Please proceed to payment.",
        notification_type="ride_completed",
    )
    db.commit()
    db.refresh(ride)
    return _ride_response(db, ride)


@router.post("/{ride_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    ride_id: uuid.UUID,
    request: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER)),
) -> PaymentResponse:
    ride = db.get(RideModel, ride_id)
    if not ride or ride.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    amount = ride.final_fare or ride.estimated_fare
    if amount is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride fare is not available")
    existing_payment = db.scalar(
        select(PaymentModel).where(
            PaymentModel.ride_id == ride.id,
            PaymentModel.deleted_at.is_(None),
        )
    )
    if existing_payment:
        return PaymentResponse.model_validate(existing_payment)

    payment = PaymentModel(ride_id=ride.id, payer_user_id=current_user.id, amount=amount, currency=ride.currency, payment_status="paid", paid_at=datetime.now(UTC), **request.model_dump())
    db.add(payment)
    NotificationService(db).send(
        user_id=current_user.id,
        title="Payment successful",
        message=f"Payment of {ride.currency} {amount} was completed.",
        notification_type="payment_paid",
    )
    db.commit()
    db.refresh(payment)
    return PaymentResponse.model_validate(payment)


@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def rate_ride(
    request: RatingCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER, UserRole.DRIVER)),
) -> RatingResponse:
    ride = db.get(RideModel, request.ride_id)
    if not ride or ride.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only completed rides can be rated")
    if current_user.role == UserRole.CUSTOMER:
        if ride.customer_id != current_user.id or request.rated_user_id != _driver_user_id(db, ride):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer can only rate their ride driver")
    elif current_user.role == UserRole.DRIVER:
        driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
        if not driver or ride.driver_id != driver.id or request.rated_user_id != ride.customer_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver can only rate their ride customer")
    rating = RatingModel(rated_by_user_id=current_user.id, **request.model_dump())
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return RatingResponse.model_validate(rating)


@router.post("/{ride_id}/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def rate_completed_ride(
    ride_id: uuid.UUID,
    request: RideRatingCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_roles(UserRole.CUSTOMER, UserRole.DRIVER)),
) -> RatingResponse:
    ride = db.get(RideModel, ride_id)
    if not ride or ride.deleted_at is not None or ride.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only completed rides can be rated")

    if current_user.role == UserRole.CUSTOMER:
        if ride.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ride does not belong to this customer")
        rated_user_id = _driver_user_id(db, ride)
        if not rated_user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ride has no driver to rate")
    else:
        driver = db.scalar(select(DriverModel).where(DriverModel.user_id == current_user.id, DriverModel.deleted_at.is_(None)))
        if not driver or ride.driver_id != driver.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ride is not assigned to this driver")
        rated_user_id = ride.customer_id

    rating = RatingModel(
        ride_id=ride.id,
        rated_by_user_id=current_user.id,
        rated_user_id=rated_user_id,
        rating=request.rating,
        comment=request.comment,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return RatingResponse.model_validate(rating)


def _driver_user_id(db: Session, ride: RideModel) -> uuid.UUID | None:
    if not ride.driver_id:
        return None
    driver = db.get(DriverModel, ride.driver_id)
    return driver.user_id if driver else None


def _ride_response(db: Session, ride: RideModel) -> RideResponse:
    response = RideResponse.model_validate(ride)
    if ride.driver_id:
        driver = db.get(DriverModel, ride.driver_id)
        if driver:
            driver_user = db.get(UserModel, driver.user_id)
            if driver_user:
                response.driver_details = RideDriverDetailsResponse(
                    id=driver.id,
                    user_id=driver.user_id,
                    full_name=driver_user.full_name,
                    phone_number=driver_user.phone_number,
                    average_rating=float(driver.average_rating) if driver.average_rating is not None else None,
                    total_rides=driver.total_rides,
                    created_at=driver.created_at,
                    updated_at=driver.updated_at,
                )
    if ride.vehicle_id:
        vehicle = db.get(VehicleModel, ride.vehicle_id)
        if vehicle:
            response.vehicle_details = RideVehicleDetailsResponse(
                id=vehicle.id,
                vehicle_type=vehicle.vehicle_type,
                make=vehicle.make,
                model=vehicle.model,
                color=vehicle.color,
                registration_number=vehicle.registration_number,
                created_at=vehicle.created_at,
                updated_at=vehicle.updated_at,
            )
    return response


def _accepted_driver_message(db: Session, driver: DriverModel, vehicle: VehicleModel) -> str:
    driver_user = db.get(UserModel, driver.user_id)
    driver_name = driver_user.full_name if driver_user else "Your driver"
    driver_phone = driver_user.phone_number if driver_user else "not available"
    vehicle_name = f"{vehicle.color} {vehicle.make} {vehicle.model}"
    return (
        f"{driver_name} accepted your ride and is heading to pickup. "
        f"Phone: {driver_phone}. Vehicle: {vehicle_name}, number {vehicle.registration_number}."
    )
