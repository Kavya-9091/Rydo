from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models.driver_model import DriverModel
from app.infrastructure.database.models.vehicle_model import VehicleModel
from app.services.fare_calculation_service import FareCalculationService


class RideMatchingService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._fare = FareCalculationService()

    def find_nearest_driver(self, ride_type: str, pickup_latitude: float, pickup_longitude: float) -> tuple[DriverModel, VehicleModel] | None:
        rows = self._eligible_driver_rows(ride_type)
        if not rows:
            return None

        return min(
            rows,
            key=lambda row: self._fare.distance_km(
                float(row[0].current_latitude),
                float(row[0].current_longitude),
                pickup_latitude,
                pickup_longitude,
            ),
        )

    def find_nearby_vehicles(
        self,
        *,
        pickup_latitude: float,
        pickup_longitude: float,
        ride_type: str | None = None,
        limit: int = 12,
    ) -> list[dict[str, object]]:
        rows = self._eligible_driver_rows(ride_type)
        ranked = []
        for driver, vehicle in rows:
            distance = self._fare.distance_km(
                float(driver.current_latitude),
                float(driver.current_longitude),
                pickup_latitude,
                pickup_longitude,
            )
            ranked.append(
                {
                    "driver_id": driver.id,
                    "vehicle_id": vehicle.id,
                    "vehicle_type": vehicle.vehicle_type,
                    "distance_km": round(distance, 2),
                    "eta_minutes": max(1, round((distance / 22) * 60)),
                    "current_latitude": float(driver.current_latitude),
                    "current_longitude": float(driver.current_longitude),
                }
            )

        return sorted(ranked, key=lambda item: item["distance_km"])[:limit]

    def _eligible_driver_rows(self, ride_type: str | None) -> list[tuple[DriverModel, VehicleModel]]:
        statement = (
            select(DriverModel, VehicleModel)
            .join(VehicleModel, VehicleModel.driver_id == DriverModel.id)
            .where(
                DriverModel.deleted_at.is_(None),
                DriverModel.approval_status == "approved",
                DriverModel.availability_status == "online",
                VehicleModel.deleted_at.is_(None),
                VehicleModel.is_active.is_(True),
                VehicleModel.approval_status == "approved",
                DriverModel.current_latitude.is_not(None),
                DriverModel.current_longitude.is_not(None),
            )
        )
        if ride_type:
            statement = statement.where(VehicleModel.vehicle_type == ride_type)
        return self._db.execute(statement).all()
