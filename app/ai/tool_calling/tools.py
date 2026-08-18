import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.ai.tool_calling.registry import ToolRegistry
from app.ai.tool_calling.schemas import ToolDefinition, ToolExecutionContext, ToolResult
from app.infrastructure.database.models.driver_model import DriverModel
from app.infrastructure.database.models.payment_model import PaymentModel
from app.infrastructure.database.models.rating_model import RatingModel
from app.infrastructure.database.models.ride_model import RideModel
from app.infrastructure.database.models.ride_rejection_model import RideRejectionModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.vehicle_model import VehicleModel
from app.infrastructure.services.notification_service import NotificationService
from app.services.fare_calculation_service import FareCalculationService
from app.services.ride_matching_service import RideMatchingService

VALID_VEHICLE_TYPES = {"bike", "auto", "mini", "sedan", "suv", "luxury"}


def create_ride_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for definition, handler in [
        (_book_ride_definition(), book_ride),
        (_cancel_ride_definition(), cancel_ride),
        (_get_ride_status_definition(), get_ride_status),
        (_ride_history_definition(), ride_history),
        (_estimate_fare_definition(), estimate_fare),
        (_nearest_driver_definition(), nearest_driver),
        (_get_driver_location_definition(), get_driver_location),
        (_rate_ride_definition(), rate_ride),
        (_payment_status_definition(), payment_status),
        (_accept_ride_definition(), accept_ride),
        (_reject_ride_definition(), reject_ride),
        (_start_ride_definition(), start_ride),
        (_complete_ride_definition(), complete_ride),
        (_approve_vehicles_definition(), approve_vehicles),
    ]:
        registry.register(definition, handler)
    return registry


def book_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    missing = _missing(arguments, ["pickup_address", "pickup_latitude", "pickup_longitude", "dropoff_address", "dropoff_latitude", "dropoff_longitude", "ride_time", "vehicle_type"])
    if missing:
        return ToolResult(success=False, message=f"Missing required booking details: {', '.join(missing)}")
    vehicle_type = arguments["vehicle_type"]
    if vehicle_type not in VALID_VEHICLE_TYPES:
        return ToolResult(success=False, message="Invalid vehicle type", data={"valid_vehicle_types": sorted(VALID_VEHICLE_TYPES)})

    fare_service = FareCalculationService()
    distance = fare_service.distance_km(arguments["pickup_latitude"], arguments["pickup_longitude"], arguments["dropoff_latitude"], arguments["dropoff_longitude"])
    estimated_fare = fare_service.estimate_fare(vehicle_type, distance)
    match = RideMatchingService(context.db).find_nearest_driver(vehicle_type, arguments["pickup_latitude"], arguments["pickup_longitude"])
    ride = RideModel(
        customer_id=context.user.id,
        driver_id=match[0].id if match else None,
        vehicle_id=match[1].id if match else None,
        status="requested",
        ride_type=vehicle_type,
        pickup_address=arguments["pickup_address"],
        pickup_latitude=arguments["pickup_latitude"],
        pickup_longitude=arguments["pickup_longitude"],
        dropoff_address=arguments["dropoff_address"],
        dropoff_latitude=arguments["dropoff_latitude"],
        dropoff_longitude=arguments["dropoff_longitude"],
        estimated_distance_km=distance,
        estimated_fare=estimated_fare,
    )
    context.db.add(ride)
    notifier = NotificationService(context.db)
    notifier.send(
        user_id=context.user.id,
        title="Ride requested",
        message="We are finding a driver for your trip.",
        notification_type="ride_requested",
    )
    if match:
        notifier.send(
            user_id=match[0].user_id,
            title="New ride request",
            message=f"Pickup: {arguments['pickup_address']}",
            notification_type="ride_requested",
        )
    context.db.commit()
    context.db.refresh(ride)
    return ToolResult(
        success=True,
        message="Ride requested successfully. Waiting for driver acceptance.",
        data=_ride_data(ride),
    )


def cancel_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    ride = _get_user_ride(arguments.get("ride_id"), context)
    if not ride:
        return ToolResult(success=False, message="Ride not found")
    if ride.status in {"completed", "cancelled"}:
        return ToolResult(success=False, message=f"Ride cannot be cancelled because it is {ride.status}")
    ride.status = "cancelled"
    ride.cancelled_at = datetime.now(UTC)
    ride.cancellation_reason = arguments.get("reason", "Cancelled by customer")
    if ride.driver_id:
        driver = context.db.get(DriverModel, ride.driver_id)
        if driver:
            driver.availability_status = "online"
            NotificationService(context.db).send(
                user_id=driver.user_id,
                title="Ride cancelled",
                message=ride.cancellation_reason,
                notification_type="ride_cancelled",
            )
    NotificationService(context.db).send(
        user_id=ride.customer_id,
        title="Ride cancelled",
        message=ride.cancellation_reason,
        notification_type="ride_cancelled",
    )
    context.db.commit()
    context.db.refresh(ride)
    return ToolResult(success=True, message="Ride cancelled successfully", data=_ride_data(ride))


def get_ride_status(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    ride = _get_user_ride(arguments.get("ride_id"), context)
    if not ride:
        return ToolResult(success=False, message="Ride not found")
    return ToolResult(success=True, message=f"Ride status is {ride.status}", data=_ride_data(ride, context.db))


def ride_history(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    limit = int(arguments.get("limit", 5))
    rides = context.db.scalars(
        select(RideModel)
        .where(RideModel.customer_id == context.user.id, RideModel.deleted_at.is_(None))
        .order_by(RideModel.requested_at.desc())
        .limit(min(limit, 20))
    ).all()
    return ToolResult(success=True, message="Ride history retrieved", data={"rides": [_ride_data(ride) for ride in rides]})


def estimate_fare(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    missing = _missing(arguments, ["pickup_latitude", "pickup_longitude", "dropoff_latitude", "dropoff_longitude", "vehicle_type"])
    if missing:
        return ToolResult(success=False, message=f"Missing required fare details: {', '.join(missing)}")
    vehicle_type = arguments["vehicle_type"]
    if vehicle_type not in VALID_VEHICLE_TYPES:
        return ToolResult(success=False, message="Invalid vehicle type", data={"valid_vehicle_types": sorted(VALID_VEHICLE_TYPES)})
    service = FareCalculationService()
    distance = service.distance_km(arguments["pickup_latitude"], arguments["pickup_longitude"], arguments["dropoff_latitude"], arguments["dropoff_longitude"])
    fare = service.estimate_fare(vehicle_type, distance)
    return ToolResult(success=True, message="Fare estimated", data={"distance_km": distance, "estimated_fare": fare, "currency": "INR", "vehicle_type": vehicle_type})


def nearest_driver(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    missing = _missing(arguments, ["pickup_latitude", "pickup_longitude", "vehicle_type"])
    if missing:
        return ToolResult(success=False, message=f"Missing driver search details: {', '.join(missing)}")
    match = RideMatchingService(context.db).find_nearest_driver(arguments["vehicle_type"], arguments["pickup_latitude"], arguments["pickup_longitude"])
    if not match:
        return ToolResult(success=False, message="No nearby approved online driver found")
    driver, vehicle = match
    distance = FareCalculationService().distance_km(
        float(driver.current_latitude),
        float(driver.current_longitude),
        arguments["pickup_latitude"],
        arguments["pickup_longitude"],
    )
    return ToolResult(
        success=True,
        message="Nearest driver found",
        data={
            "driver_id": str(driver.id),
            "vehicle_id": str(vehicle.id),
            "latitude": float(driver.current_latitude),
            "longitude": float(driver.current_longitude),
            "distance_km": round(distance, 2),
            "eta_minutes": max(1, round((distance / 22) * 60)),
        },
    )


def get_driver_location(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    ride = _get_user_ride(arguments.get("ride_id"), context)
    if not ride or not ride.driver_id:
        return ToolResult(success=False, message="Driver is not assigned to this ride")
    driver = context.db.get(DriverModel, ride.driver_id)
    if not driver or driver.current_latitude is None or driver.current_longitude is None:
        return ToolResult(success=False, message="Driver location is unavailable")
    return ToolResult(success=True, message="Driver location retrieved", data={"driver_id": str(driver.id), "latitude": float(driver.current_latitude), "longitude": float(driver.current_longitude)})


def rate_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    missing = _missing(arguments, ["ride_id", "rating"])
    if missing:
        return ToolResult(success=False, message=f"Missing rating details: {', '.join(missing)}")
    ride = _get_user_ride(arguments["ride_id"], context)
    if not ride or ride.status != "completed":
        return ToolResult(success=False, message="Only completed rides can be rated")
    rating_value = int(arguments["rating"])
    if rating_value < 1 or rating_value > 5:
        return ToolResult(success=False, message="Rating must be between 1 and 5")
    rated_user_id = arguments.get("rated_user_id")
    if not rated_user_id:
        rated_user_id = str(_driver_user_id(context.db, ride))
    if not rated_user_id or rated_user_id == "None":
        return ToolResult(success=False, message="Ride has no driver to rate")
    rating = RatingModel(ride_id=ride.id, rated_by_user_id=context.user.id, rated_user_id=uuid.UUID(str(rated_user_id)), rating=rating_value, comment=arguments.get("comment"))
    context.db.add(rating)
    context.db.commit()
    context.db.refresh(rating)
    return ToolResult(success=True, message="Rating submitted", data={"rating_id": str(rating.id), "rating": rating.rating})


def payment_status(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    ride = _get_user_ride(arguments.get("ride_id"), context)
    if not ride:
        return ToolResult(success=False, message="Ride not found")
    payment = context.db.scalar(select(PaymentModel).where(PaymentModel.ride_id == ride.id, PaymentModel.deleted_at.is_(None)))
    if not payment:
        return ToolResult(success=False, message="No payment found for this ride")
    return ToolResult(success=True, message=f"Payment status is {payment.payment_status}", data={"payment_id": str(payment.id), "status": payment.payment_status, "amount": float(payment.amount), "currency": payment.currency})


def accept_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    if context.user.role != "driver":
        return ToolResult(success=False, message="Only drivers can accept rides")
    driver = _current_driver(context)
    if not driver:
        return ToolResult(success=False, message="Driver profile not found")
    ride = _driver_ride(arguments.get("ride_id"), context, driver)
    if not ride:
        return ToolResult(success=False, message="No recent ride is waiting for you to accept")
    if ride.status != "requested":
        return ToolResult(success=False, message=f"Ride cannot be accepted because it is {ride.status}")
    vehicle = context.db.scalar(
        select(VehicleModel).where(
            VehicleModel.driver_id == driver.id,
            VehicleModel.deleted_at.is_(None),
            VehicleModel.is_active.is_(True),
            VehicleModel.approval_status == "approved",
            VehicleModel.vehicle_type == ride.ride_type,
        )
    )
    if not vehicle:
        return ToolResult(success=False, message="No approved matching vehicle found")
    ride.driver_id = driver.id
    ride.vehicle_id = vehicle.id
    ride.status = "accepted"
    ride.accepted_at = datetime.now(UTC)
    driver.availability_status = "busy"
    NotificationService(context.db).send(
        user_id=ride.customer_id,
        title="Driver accepted",
        message="Your driver accepted the ride and is heading to pickup.",
        notification_type="ride_accepted",
    )
    context.db.commit()
    context.db.refresh(ride)
    return ToolResult(success=True, message="Ride accepted", data=_ride_data(ride))


def reject_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    if context.user.role != "driver":
        return ToolResult(success=False, message="Only drivers can reject rides")
    driver = _current_driver(context)
    if not driver:
        return ToolResult(success=False, message="Driver profile not found")
    ride = _driver_ride(arguments.get("ride_id"), context, driver)
    if not ride:
        return ToolResult(success=False, message="No recent ride is available to reject")
    if ride.status not in {"requested", "accepted"}:
        return ToolResult(success=False, message=f"Ride cannot be rejected because it is {ride.status}")
    if ride.driver_id is None and ride.status == "requested":
        _record_ride_rejection(context, ride, driver, arguments.get("reason"))
        context.db.commit()
        context.db.refresh(ride)
        return ToolResult(success=True, message="Ride offer declined", data=_ride_data(ride))
    if ride.driver_id != driver.id:
        return ToolResult(success=False, message="Ride is assigned to another driver")
    ride.driver_id = None
    ride.vehicle_id = None
    ride.status = "requested"
    ride.accepted_at = None
    driver.availability_status = "online"
    NotificationService(context.db).send(
        user_id=ride.customer_id,
        title="Driver unavailable",
        message="Your driver could not continue. We are looking for another driver.",
        notification_type="ride_rejected",
    )
    context.db.commit()
    context.db.refresh(ride)
    return ToolResult(success=True, message="Ride rejected", data=_ride_data(ride))


def start_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    if context.user.role != "driver":
        return ToolResult(success=False, message="Only drivers can start rides")
    driver = _current_driver(context)
    if not driver:
        return ToolResult(success=False, message="Driver profile not found")
    ride = _driver_ride(arguments.get("ride_id"), context, driver, statuses={"accepted"})
    if not ride:
        return ToolResult(success=False, message="No accepted ride is ready to start")
    if ride.driver_id != driver.id:
        return ToolResult(success=False, message="Ride is not assigned to this driver")
    ride.status = "in_progress"
    ride.started_at = datetime.now(UTC)
    NotificationService(context.db).send(
        user_id=ride.customer_id,
        title="Ride started",
        message="Your ride is now in progress.",
        notification_type="ride_started",
    )
    context.db.commit()
    context.db.refresh(ride)
    return ToolResult(success=True, message="Ride started", data=_ride_data(ride))


def complete_ride(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    if context.user.role != "driver":
        return ToolResult(success=False, message="Only drivers can complete rides")
    driver = _current_driver(context)
    if not driver:
        return ToolResult(success=False, message="Driver profile not found")
    ride = _driver_ride(arguments.get("ride_id"), context, driver, statuses={"in_progress"})
    if not ride:
        return ToolResult(success=False, message="No active ride is ready to complete")
    if ride.driver_id != driver.id:
        return ToolResult(success=False, message="Ride is not assigned to this driver")
    ride.status = "completed"
    ride.completed_at = datetime.now(UTC)
    ride.final_fare = ride.estimated_fare
    driver.availability_status = "online"
    driver.total_rides += 1
    NotificationService(context.db).send(
        user_id=ride.customer_id,
        title="Ride completed",
        message="Your ride is complete. Please proceed to payment.",
        notification_type="ride_completed",
    )
    context.db.commit()
    context.db.refresh(ride)
    return ToolResult(success=True, message="Ride completed", data=_ride_data(ride))


def approve_vehicles(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    if context.user.role != "admin":
        return ToolResult(success=False, message="Only admins can approve vehicles")
    registration_numbers = [
        str(number).strip().upper()
        for number in arguments.get("registration_numbers", [])
        if str(number).strip()
    ]
    if not registration_numbers:
        return ToolResult(success=False, message="Please share at least one vehicle registration number")

    vehicles = context.db.scalars(
        select(VehicleModel).where(
            VehicleModel.registration_number.in_(registration_numbers),
            VehicleModel.deleted_at.is_(None),
        )
    ).all()
    found_numbers = {vehicle.registration_number for vehicle in vehicles}
    approved = []
    for vehicle in vehicles:
        vehicle.approval_status = "approved"
        approved.append(vehicle.registration_number)
    context.db.commit()
    return ToolResult(
        success=True,
        message="Vehicle approvals updated",
        data={
            "approved": approved,
            "not_found": [number for number in registration_numbers if number not in found_numbers],
        },
    )


def _get_user_ride(ride_id: Any, context: ToolExecutionContext) -> RideModel | None:
    if not ride_id:
        return None
    try:
        parsed_id = uuid.UUID(str(ride_id))
    except ValueError:
        return None
    return context.db.scalar(select(RideModel).where(RideModel.id == parsed_id, RideModel.customer_id == context.user.id, RideModel.deleted_at.is_(None)))


def _current_driver(context: ToolExecutionContext) -> DriverModel | None:
    return context.db.scalar(
        select(DriverModel).where(
            DriverModel.user_id == context.user.id,
            DriverModel.deleted_at.is_(None),
        )
    )


def _driver_ride(
    ride_id: Any,
    context: ToolExecutionContext,
    driver: DriverModel,
    statuses: set[str] | None = None,
) -> RideModel | None:
    allowed_statuses = statuses or {"requested"}
    rejected_ride_ids = select(RideRejectionModel.ride_id).where(
        RideRejectionModel.driver_id == driver.id,
        RideRejectionModel.deleted_at.is_(None),
    )
    if ride_id:
        try:
            parsed_id = uuid.UUID(str(ride_id))
        except ValueError:
            return None
        return context.db.scalar(
            select(RideModel).where(
                RideModel.id == parsed_id,
                RideModel.deleted_at.is_(None),
                RideModel.id.not_in(rejected_ride_ids),
                RideModel.status.in_(allowed_statuses),
            )
        )
    return context.db.scalar(
        select(RideModel)
        .where(
            RideModel.deleted_at.is_(None),
            RideModel.id.not_in(rejected_ride_ids),
            RideModel.status.in_(allowed_statuses),
            _driver_ride_assignment_filter(driver, allowed_statuses),
        )
        .order_by(RideModel.requested_at.desc())
    )


def _driver_ride_assignment_filter(driver: DriverModel, statuses: set[str]) -> Any:
    if statuses == {"requested"}:
        return (RideModel.driver_id == driver.id) | (RideModel.driver_id.is_(None))
    return RideModel.driver_id == driver.id


def _record_ride_rejection(context: ToolExecutionContext, ride: RideModel, driver: DriverModel, reason: Any = None) -> None:
    existing_rejection = context.db.scalar(
        select(RideRejectionModel).where(
            RideRejectionModel.ride_id == ride.id,
            RideRejectionModel.driver_id == driver.id,
            RideRejectionModel.deleted_at.is_(None),
        )
    )
    if existing_rejection:
        return
    context.db.add(
        RideRejectionModel(
            ride_id=ride.id,
            driver_id=driver.id,
            reason=str(reason) if reason else None,
            source="ai",
        )
    )


def get_ride_history(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    return ride_history(arguments, context)


def find_nearest_driver(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    return nearest_driver(arguments, context)


def get_payment_status(arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
    return payment_status(arguments, context)


def _driver_user_id(db: Any, ride: RideModel) -> uuid.UUID | None:
    if not ride.driver_id:
        return None
    driver = db.get(DriverModel, ride.driver_id)
    return driver.user_id if driver else None


def _missing(arguments: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if arguments.get(field) in (None, "")]


def _ride_data(ride: RideModel, db: Any | None = None) -> dict[str, Any]:
    data = {
        "ride_id": str(ride.id),
        "status": ride.status,
        "vehicle_type": ride.ride_type,
        "driver_id": str(ride.driver_id) if ride.driver_id else None,
        "vehicle_id": str(ride.vehicle_id) if ride.vehicle_id else None,
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
        "estimated_distance_km": float(ride.estimated_distance_km) if ride.estimated_distance_km is not None else None,
        "estimated_fare": float(ride.estimated_fare) if ride.estimated_fare is not None else None,
        "final_fare": float(ride.final_fare) if ride.final_fare is not None else None,
        "currency": ride.currency,
    }
    if db and ride.driver_id:
        driver = db.get(DriverModel, ride.driver_id)
        driver_user = db.get(UserModel, driver.user_id) if driver else None
        if driver and driver_user:
            data["driver_details"] = {
                "driver_name": driver_user.full_name,
                "phone_number": driver_user.phone_number,
                "average_rating": float(driver.average_rating) if driver.average_rating is not None else None,
                "total_rides": driver.total_rides,
            }
    if db and ride.vehicle_id:
        vehicle = db.get(VehicleModel, ride.vehicle_id)
        if vehicle:
            data["vehicle_details"] = {
                "vehicle_type": vehicle.vehicle_type,
                "make": vehicle.make,
                "model": vehicle.model,
                "color": vehicle.color,
                "registration_number": vehicle.registration_number,
            }
    return data


def _object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required or [], "additionalProperties": False}


def _book_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="book_ride", description="Book a ride for the authenticated customer.", parameters=_object(_location_props() | {"ride_time": {"type": "string"}, "vehicle_type": _vehicle_type_schema()}, ["pickup_address", "pickup_latitude", "pickup_longitude", "dropoff_address", "dropoff_latitude", "dropoff_longitude", "ride_time", "vehicle_type"]))


def _cancel_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="cancel_ride", description="Cancel one of the customer's active rides.", parameters=_object({"ride_id": {"type": "string"}, "reason": {"type": "string"}}, ["ride_id"]))


def _get_ride_status_definition() -> ToolDefinition:
    return ToolDefinition(name="get_ride_status", description="Get current status for a ride.", parameters=_object({"ride_id": {"type": "string"}}, ["ride_id"]))


def _ride_history_definition() -> ToolDefinition:
    return ToolDefinition(name="ride_history", description="Get recent ride history.", parameters=_object({"limit": {"type": "integer", "minimum": 1, "maximum": 20}}))


def _estimate_fare_definition() -> ToolDefinition:
    return ToolDefinition(name="estimate_fare", description="Estimate fare for a route and vehicle type.", parameters=_object({k: v for k, v in _location_props().items() if k != "pickup_address" and k != "dropoff_address"} | {"vehicle_type": _vehicle_type_schema()}, ["pickup_latitude", "pickup_longitude", "dropoff_latitude", "dropoff_longitude", "vehicle_type"]))


def _nearest_driver_definition() -> ToolDefinition:
    return ToolDefinition(name="nearest_driver", description="Find nearest approved online driver for a pickup.", parameters=_object({"pickup_latitude": {"type": "number"}, "pickup_longitude": {"type": "number"}, "vehicle_type": _vehicle_type_schema()}, ["pickup_latitude", "pickup_longitude", "vehicle_type"]))


def _get_driver_location_definition() -> ToolDefinition:
    return ToolDefinition(name="get_driver_location", description="Get assigned driver location for a ride.", parameters=_object({"ride_id": {"type": "string"}}, ["ride_id"]))


def _rate_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="rate_ride", description="Rate a completed ride. For customers, rated_user_id can be omitted and the assigned driver is rated.", parameters=_object({"ride_id": {"type": "string"}, "rated_user_id": {"type": "string"}, "rating": {"type": "integer", "minimum": 1, "maximum": 5}, "comment": {"type": "string"}}, ["ride_id", "rating"]))


def _payment_status_definition() -> ToolDefinition:
    return ToolDefinition(name="payment_status", description="Get payment status for a ride.", parameters=_object({"ride_id": {"type": "string"}}, ["ride_id"]))


def _accept_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="accept_ride", description="Accept the driver's assigned or most recent available ride.", parameters=_object({"ride_id": {"type": "string"}}))


def _reject_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="reject_ride", description="Reject the driver's assigned or most recent available ride.", parameters=_object({"ride_id": {"type": "string"}}))


def _start_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="start_ride", description="Start the driver's accepted ride.", parameters=_object({"ride_id": {"type": "string"}}))


def _complete_ride_definition() -> ToolDefinition:
    return ToolDefinition(name="complete_ride", description="Complete the driver's active ride.", parameters=_object({"ride_id": {"type": "string"}}))


def _approve_vehicles_definition() -> ToolDefinition:
    return ToolDefinition(
        name="approve_vehicles",
        description="Approve one or more vehicles by registration number. Admin only.",
        parameters=_object(
            {"registration_numbers": {"type": "array", "items": {"type": "string"}}},
            ["registration_numbers"],
        ),
    )


def _location_props() -> dict[str, Any]:
    return {"pickup_address": {"type": "string"}, "pickup_latitude": {"type": "number"}, "pickup_longitude": {"type": "number"}, "dropoff_address": {"type": "string"}, "dropoff_latitude": {"type": "number"}, "dropoff_longitude": {"type": "number"}}


def _vehicle_type_schema() -> dict[str, Any]:
    return {"type": "string", "enum": sorted(VALID_VEHICLE_TYPES)}
