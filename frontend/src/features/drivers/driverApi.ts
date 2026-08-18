import { apiClient } from "../../lib/apiClient";
import type { AuthUser } from "../../types/auth";
import type { Ride } from "../../types/ride";

export interface DriverProfile {
  id: string;
  user_id: string;
  approval_status: string;
  availability_status: string;
  current_latitude: number | null;
  current_longitude: number | null;
  average_rating: number | null;
  total_rides: number;
  created_at: string;
  updated_at: string;
}

export interface Vehicle {
  id: string;
  driver_id: string;
  vehicle_type: "bike" | "auto" | "mini" | "sedan" | "suv" | "luxury";
  make: string;
  model: string;
  color: string;
  registration_number: string;
  capacity: number;
  approval_status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VehiclePayload {
  vehicle_type: Vehicle["vehicle_type"];
  make: string;
  model: string;
  color: string;
  registration_number: string;
  capacity: number;
}

export async function registerDriver(): Promise<DriverProfile> {
  const response = await apiClient.post<DriverProfile>("/drivers/register");
  return response.data;
}

export async function getDriverProfile(): Promise<DriverProfile> {
  const response = await apiClient.get<DriverProfile>("/drivers/me");
  return response.data;
}

export async function goOnline(latitude: number, longitude: number): Promise<DriverProfile> {
  const response = await apiClient.post<DriverProfile>("/drivers/online", { latitude, longitude });
  return response.data;
}

export async function goOffline(): Promise<DriverProfile> {
  const response = await apiClient.post<DriverProfile>("/drivers/offline");
  return response.data;
}

export async function registerVehicle(payload: VehiclePayload): Promise<Vehicle> {
  const response = await apiClient.post<Vehicle>("/drivers/vehicles", payload);
  return response.data;
}

export async function listAssignedRides(): Promise<Ride[]> {
  const response = await apiClient.get<Ride[]>("/drivers/rides");
  return response.data;
}

export async function listDrivers(): Promise<DriverProfile[]> {
  const response = await apiClient.get<DriverProfile[]>("/admin/drivers");
  return response.data;
}

export async function listUsers(): Promise<AuthUser[]> {
  const response = await apiClient.get<AuthUser[]>("/admin/users");
  return response.data;
}

export async function listVehicles(): Promise<Vehicle[]> {
  const response = await apiClient.get<Vehicle[]>("/admin/vehicles");
  return response.data;
}

export async function approveDriver(driverId: string): Promise<DriverProfile> {
  const response = await apiClient.post<DriverProfile>(`/admin/drivers/${driverId}/approve`);
  return response.data;
}

export async function approveVehicle(vehicleId: string): Promise<Vehicle> {
  const response = await apiClient.post<Vehicle>(`/admin/vehicles/${vehicleId}/approve`);
  return response.data;
}
