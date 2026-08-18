import type { VehicleType } from "../../types/ride";

const BASE_FARES: Record<VehicleType, number> = {
  bike: 25,
  auto: 35,
  mini: 50,
  sedan: 75,
  suv: 110,
  luxury: 180,
};

const PER_KM: Record<VehicleType, number> = {
  bike: 8,
  auto: 11,
  mini: 14,
  sedan: 18,
  suv: 24,
  luxury: 40,
};

export function distanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const radiusKm = 6371;
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLon / 2) ** 2;
  return Number((2 * radiusKm * Math.asin(Math.sqrt(a))).toFixed(2));
}

export function estimateFare(vehicleType: VehicleType, distance: number): number {
  return Number((BASE_FARES[vehicleType] + distance * PER_KM[vehicleType]).toFixed(2));
}

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}
