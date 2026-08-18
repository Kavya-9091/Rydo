import { apiClient } from "../../lib/apiClient";
import type { NearbyVehicle, Notification, Payment, Rating, Ride, RideCreatePayload, VehicleType } from "../../types/ride";

export async function bookRide(payload: RideCreatePayload): Promise<Ride> {
  const response = await apiClient.post<Ride>("/rides", payload);
  return response.data;
}

export async function getRide(rideId: string): Promise<Ride> {
  const response = await apiClient.get<Ride>(`/rides/${rideId}`);
  return response.data;
}

export async function getRideHistory(): Promise<Ride[]> {
  const response = await apiClient.get<Ride[]>("/customers/rides");
  return response.data;
}

export async function getNearbyVehicles(
  pickupLatitude: number,
  pickupLongitude: number,
  rideType?: VehicleType,
): Promise<NearbyVehicle[]> {
  const response = await apiClient.get<NearbyVehicle[]>("/rides/nearby-vehicles", {
    params: {
      pickup_latitude: pickupLatitude,
      pickup_longitude: pickupLongitude,
      ride_type: rideType,
    },
  });
  return response.data;
}

export async function cancelRide(rideId: string, reason: string): Promise<Ride> {
  const response = await apiClient.post<Ride>(`/rides/${rideId}/cancel`, { reason });
  return response.data;
}

export async function acceptRide(rideId: string): Promise<Ride> {
  const response = await apiClient.post<Ride>(`/rides/${rideId}/accept`);
  return response.data;
}

export async function startRide(rideId: string): Promise<Ride> {
  const response = await apiClient.post<Ride>(`/rides/${rideId}/start`);
  return response.data;
}

export async function completeRide(rideId: string): Promise<Ride> {
  const response = await apiClient.post<Ride>(`/rides/${rideId}/complete`);
  return response.data;
}

export async function rejectRide(rideId: string): Promise<Ride> {
  const response = await apiClient.post<Ride>(`/rides/${rideId}/reject`);
  return response.data;
}

export async function createPayment(rideId: string, paymentMethod: string): Promise<Payment> {
  const response = await apiClient.post<Payment>(`/rides/${rideId}/payments`, {
    payment_method: paymentMethod,
    provider: "demo",
  });
  return response.data;
}

export async function getPaymentHistory(): Promise<Payment[]> {
  const response = await apiClient.get<Payment[]>("/customers/payments");
  return response.data;
}

export async function rateRide(rideId: string, rating: number, comment?: string): Promise<Rating> {
  const response = await apiClient.post<Rating>(`/rides/${rideId}/ratings`, {
    rating,
    comment: comment || null,
  });
  return response.data;
}

export async function getNotifications(): Promise<Notification[]> {
  const response = await apiClient.get<Notification[]>("/notifications");
  return response.data;
}

export async function markNotificationRead(notificationId: string): Promise<Notification> {
  const response = await apiClient.post<Notification>(`/notifications/${notificationId}/read`);
  return response.data;
}
