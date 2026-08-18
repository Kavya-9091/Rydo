export type VehicleType = "bike" | "auto" | "mini" | "sedan" | "suv" | "luxury";

export interface RideCreatePayload {
  ride_type: VehicleType;
  pickup_address: string;
  pickup_latitude: number;
  pickup_longitude: number;
  dropoff_address: string;
  dropoff_latitude: number;
  dropoff_longitude: number;
  rider_name?: string | null;
  rider_phone_number?: string | null;
}

export interface NearbyVehicle {
  driver_id: string;
  vehicle_id: string;
  vehicle_type: VehicleType;
  distance_km: number;
  eta_minutes: number;
  current_latitude: number;
  current_longitude: number;
}

export interface Ride {
  id: string;
  customer_id: string;
  driver_id: string | null;
  vehicle_id: string | null;
  status: "requested" | "accepted" | "in_progress" | "completed" | "cancelled";
  ride_type: VehicleType;
  pickup_address: string;
  pickup_latitude: number;
  pickup_longitude: number;
  dropoff_address: string;
  dropoff_latitude: number;
  dropoff_longitude: number;
  rider_name: string | null;
  rider_phone_number: string | null;
  estimated_distance_km: number | null;
  actual_distance_km: number | null;
  estimated_fare: number | null;
  final_fare: number | null;
  currency: string;
  requested_at: string;
  accepted_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
  driver_details: RideDriverDetails | null;
  vehicle_details: RideVehicleDetails | null;
}

export interface RideDriverDetails {
  id: string;
  user_id: string;
  full_name: string;
  phone_number: string;
  average_rating: number | null;
  total_rides: number;
  created_at: string;
  updated_at: string;
}

export interface RideVehicleDetails {
  id: string;
  vehicle_type: VehicleType;
  make: string;
  model: string;
  color: string;
  registration_number: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: string;
  ride_id: string;
  payer_user_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  payment_status: string;
  provider: string | null;
  provider_transaction_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Rating {
  id: string;
  ride_id: string;
  rated_by_user_id: string;
  rated_user_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
