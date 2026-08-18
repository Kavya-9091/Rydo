import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CarFront, CheckCircle2, Crosshair, IndianRupee, Loader2, LocateFixed, MapPin, Navigation } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation } from "react-router-dom";
import { z } from "zod";

import { MainLayout } from "../components/layout/MainLayout";
import { BookingMapSelector } from "../components/rides/BookingMapSelector";
import { LocationSearchInput } from "../components/rides/LocationSearchInput";
import { VehicleOption } from "../components/rides/VehicleOption";
import { geocodeAddress, reverseGeocode, type Coordinates } from "../features/rides/geocoding";
import { bookRide, getNearbyVehicles } from "../features/rides/rideApi";
import { distanceKm, estimateFare } from "../features/rides/farePreview";
import { usePageTitle } from "../lib/usePageTitle";
import type { Ride, VehicleType } from "../types/ride";

const vehicleTypes: VehicleType[] = ["bike", "auto", "mini", "sedan", "suv", "luxury"];

const bookingSchema = z.object({
  pickup_address: z.string().min(2, "Pickup is required"),
  dropoff_address: z.string().min(2, "Destination is required"),
  rider_name: z.string().optional(),
  rider_phone_number: z.string().optional(),
});

type BookingFormValues = z.infer<typeof bookingSchema>;
type BookingFormInput = z.input<typeof bookingSchema>;

export function HomePage() {
  usePageTitle("Book Ride");
  const location = useLocation();
  const [vehicleType, setVehicleType] = useState<VehicleType>("sedan");
  const [bookingFor, setBookingFor] = useState<"self" | "other">("self");
  const [mapMode, setMapMode] = useState<"pickup" | "destination">("pickup");
  const [bookedRide, setBookedRide] = useState<Ride | null>(null);
  const [pickupCoordinates, setPickupCoordinates] = useState<Coordinates | null>({
    latitude: 12.9756,
    longitude: 77.6068,
    displayName: "MG Road, Bengaluru",
  });
  const [dropoffCoordinates, setDropoffCoordinates] = useState<Coordinates | null>({
    latitude: 13.1986,
    longitude: 77.7066,
    displayName: "Kempegowda International Airport",
  });
  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<BookingFormInput, unknown, BookingFormValues>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      pickup_address: "MG Road, Bengaluru",
      dropoff_address: "Kempegowda International Airport",
      rider_name: "",
      rider_phone_number: "",
    },
  });
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const pickupValue = watch("pickup_address");
  const dropoffValue = watch("dropoff_address");
  const nearbyVehicles = useQuery({
    queryKey: ["nearby-vehicles", pickupCoordinates?.latitude, pickupCoordinates?.longitude, vehicleType],
    queryFn: () => getNearbyVehicles(pickupCoordinates!.latitude, pickupCoordinates!.longitude, vehicleType),
    enabled: Boolean(pickupCoordinates),
    refetchInterval: 10000,
  });

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const pickup = params.get("pickup")?.trim();
    const destination = params.get("destination")?.trim();

    if (pickup) {
      setValue("pickup_address", pickup, { shouldDirty: true, shouldValidate: true });
      geocodeAddress(pickup)
        .then(setPickupCoordinates)
        .catch(() => setPickupCoordinates(null));
    }

    if (destination) {
      setValue("dropoff_address", destination, { shouldDirty: true, shouldValidate: true });
      geocodeAddress(destination)
        .then(setDropoffCoordinates)
        .catch(() => setDropoffCoordinates(null));
    }
  }, [location.search, setValue]);

  useEffect(() => {
    function handleChatBooking(event: Event) {
      const detail = (event as CustomEvent<{
        pickup?: Coordinates;
        destination?: Coordinates;
        vehicleType?: VehicleType;
      }>).detail;
      if (!detail?.pickup || !detail.destination || !detail.vehicleType) {
        return;
      }
      setPickupCoordinates(detail.pickup);
      setDropoffCoordinates(detail.destination);
      setVehicleType(detail.vehicleType);
      setValue("pickup_address", detail.pickup.displayName, { shouldDirty: true, shouldValidate: true });
      setValue("dropoff_address", detail.destination.displayName, { shouldDirty: true, shouldValidate: true });
    }

    window.addEventListener("rydo-chat-booking-created", handleChatBooking);
    return () => window.removeEventListener("rydo-chat-booking-created", handleChatBooking);
  }, [setValue]);

  const preview = useMemo(() => {
    if (!pickupCoordinates || !dropoffCoordinates) {
      return null;
    }
    const distance = distanceKm(
      pickupCoordinates.latitude,
      pickupCoordinates.longitude,
      dropoffCoordinates.latitude,
      dropoffCoordinates.longitude,
    );
    return {
      distance,
      fare: estimateFare(vehicleType, distance),
    };
  }, [dropoffCoordinates, pickupCoordinates, vehicleType]);

  useEffect(() => {
    localStorage.setItem(
      "rydo-booking-context",
      JSON.stringify({
        pickup: pickupCoordinates,
        destination: dropoffCoordinates,
        vehicle_type: vehicleType,
      }),
    );
  }, [dropoffCoordinates, pickupCoordinates, vehicleType]);

  const mutation = useMutation({
    mutationFn: async (formValues: BookingFormValues) => {
      const pickup =
        formValues.pickup_address === pickupCoordinates?.displayName ||
        formValues.pickup_address === "Current location"
          ? pickupCoordinates
          : await geocodeAddress(formValues.pickup_address);
      const dropoff =
        formValues.dropoff_address === dropoffCoordinates?.displayName
          ? dropoffCoordinates
          : await geocodeAddress(formValues.dropoff_address);

      if (!pickup) {
        throw new Error("Choose pickup using current location or enter a searchable pickup.");
      }
      if (bookingFor === "other") {
        if (!formValues.rider_name?.trim()) {
          throw new Error("Enter rider name.");
        }
        if (!/^[6-9]\d{9}$/.test(formValues.rider_phone_number ?? "")) {
          throw new Error("Enter a valid 10 digit rider phone number.");
        }
      }

      setPickupCoordinates(pickup);
      setDropoffCoordinates(dropoff);

      return bookRide({
        ride_type: vehicleType,
        pickup_address: pickup.displayName,
        pickup_latitude: pickup.latitude,
        pickup_longitude: pickup.longitude,
        dropoff_address: dropoff.displayName,
        dropoff_latitude: dropoff.latitude,
        dropoff_longitude: dropoff.longitude,
        rider_name: bookingFor === "other" ? formValues.rider_name?.trim() : null,
        rider_phone_number: bookingFor === "other" ? formValues.rider_phone_number : null,
      });
    },
    onSuccess: setBookedRide,
  });

  function useCurrentLocation() {
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError("Current location is not supported in this browser.");
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const latitude = Number(position.coords.latitude.toFixed(7));
          const longitude = Number(position.coords.longitude.toFixed(7));
          const coordinates = await reverseGeocode(latitude, longitude);
          setPickupCoordinates(coordinates);
          setValue("pickup_address", coordinates.displayName, {
            shouldDirty: true,
            shouldValidate: true,
          });
        } catch (error) {
          setLocationError(error instanceof Error ? error.message : "Type your Bengaluru pickup.");
        } finally {
          setIsLocating(false);
        }
      },
      (error) => {
        setLocationError(
          error.message === "Rydo is currently available only in Bengaluru."
            ? error.message
            : locationErrorMessage(error),
        );
        setIsLocating(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      },
    );
  }

  return (
    <MainLayout>
      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 xl:grid-cols-[minmax(0,1fr)_520px]">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Book a ride</p>
              <h1 className="mt-2 text-3xl font-semibold text-slate-950">Where are you going?</h1>
            </div>
            <div className="rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-600">
              Fare updates as you choose a ride.
            </div>
          </div>

          <form className="grid gap-5" onSubmit={handleSubmit((data) => mutation.mutate(data))}>
            <div className="grid gap-4 lg:grid-cols-2">
              <LocationPanel
                title="Pickup"
                icon={<LocateFixed size={18} />}
                action={
                  <button
                    type="button"
                    onClick={useCurrentLocation}
                    disabled={isLocating}
                    className="flex h-8 items-center gap-2 rounded-md border border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isLocating ? <Loader2 size={14} className="animate-spin" /> : <Crosshair size={14} />}
                    Current
                  </button>
                }
                addressInput={
                  <LocationSearchInput
                    value={pickupValue}
                    placeholder="Pickup location"
                    onChange={(value) => {
                      setValue("pickup_address", value, { shouldDirty: true, shouldValidate: true });
                      setPickupCoordinates(null);
                    }}
                    onSelect={(location) => {
                      setPickupCoordinates(location);
                      setValue("pickup_address", location.displayName, { shouldDirty: true, shouldValidate: true });
                    }}
                  />
                }
                addressError={errors.pickup_address?.message ?? locationError ?? undefined}
              />

              <LocationPanel
                title="Destination"
                icon={<MapPin size={18} />}
                addressInput={
                  <LocationSearchInput
                    value={dropoffValue}
                    placeholder="Destination"
                    iconClassName="text-slate-950"
                    onChange={(value) => {
                      setValue("dropoff_address", value, { shouldDirty: true, shouldValidate: true });
                      setDropoffCoordinates(null);
                    }}
                    onSelect={(location) => {
                      setDropoffCoordinates(location);
                      setValue("dropoff_address", location.displayName, { shouldDirty: true, shouldValidate: true });
                    }}
                  />
                }
                addressError={errors.dropoff_address?.message}
              />
            </div>

            <div>
              <h2 className="mb-3 text-sm font-semibold text-slate-950">Who is riding?</h2>
              <div className="grid gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setBookingFor("self")}
                  className={`h-11 rounded-md border px-4 text-left text-sm font-semibold ${bookingFor === "self" ? "border-black bg-black text-white" : "border-slate-200 bg-white text-slate-950"}`}
                >
                  For me
                </button>
                <button
                  type="button"
                  onClick={() => setBookingFor("other")}
                  className={`h-11 rounded-md border px-4 text-left text-sm font-semibold ${bookingFor === "other" ? "border-black bg-black text-white" : "border-slate-200 bg-white text-slate-950"}`}
                >
                  Someone else
                </button>
              </div>
              {bookingFor === "other" && (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <input
                    value={watch("rider_name") ?? ""}
                    onChange={(event) => setValue("rider_name", event.target.value, { shouldDirty: true })}
                    placeholder="Rider name"
                    className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-black focus:ring-2 focus:ring-black/10"
                  />
                  <input
                    value={watch("rider_phone_number") ?? ""}
                    onChange={(event) => setValue("rider_phone_number", event.target.value.replace(/\D/g, "").slice(0, 10), { shouldDirty: true })}
                    placeholder="Rider phone"
                    inputMode="numeric"
                    className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-black focus:ring-2 focus:ring-black/10"
                  />
                </div>
              )}
            </div>

            <div>
              <h2 className="mb-3 text-sm font-semibold text-slate-950">Choose vehicle</h2>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {vehicleTypes.map((type) => (
                  <VehicleOption
                    key={type}
                    type={type}
                    selected={vehicleType === type}
                    onSelect={setVehicleType}
                  />
                ))}
              </div>
            </div>

            {mutation.error && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {mutation.error.message}
              </div>
            )}

            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex h-12 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white hover:bg-black disabled:cursor-not-allowed disabled:opacity-70"
            >
              {mutation.isPending ? <Loader2 size={18} className="animate-spin" /> : <Navigation size={18} />}
              Book ride
            </button>
          </form>
        </section>

        <aside className="space-y-4">
          <BookingMapSelector
            pickup={pickupCoordinates}
            destination={dropoffCoordinates}
            mode={mapMode}
            onModeChange={setMapMode}
          />
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-950">Fare estimate</h2>
            <div className="mt-5 flex items-end justify-between">
              <div>
                <p className="text-xs text-slate-500">Estimated fare</p>
                <p className="mt-1 flex items-center text-3xl font-semibold text-slate-950">
                  <IndianRupee size={24} />
                  {preview?.fare ?? "--"}
                </p>
              </div>
              <div className="rounded-md bg-slate-100 px-3 py-2 text-right">
                <p className="text-xs text-slate-500">Distance</p>
                <p className="text-sm font-semibold text-slate-950">{preview?.distance ?? "--"} km</p>
              </div>
            </div>
          </div>

          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-slate-950">Nearby vehicles</h2>
              {nearbyVehicles.isFetching && <Loader2 size={16} className="animate-spin text-slate-400" />}
            </div>
            <div className="mt-4 rounded-md bg-slate-50 p-4">
              <div className="flex items-center gap-3">
                <span className="flex size-10 items-center justify-center rounded-md bg-black text-white">
                  <CarFront size={20} />
                </span>
                <div>
                  <p className="text-2xl font-semibold text-slate-950">{nearbyVehicles.data?.length ?? 0}</p>
                  <p className="text-xs capitalize text-slate-500">{vehicleType} nearby</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-slate-600">
                {nearbyVehicles.data?.[0]
                  ? `Fastest pickup in ${nearbyVehicles.data[0].eta_minutes} min (${nearbyVehicles.data[0].distance_km} km away).`
                  : "No nearby approved vehicles for this option right now."}
              </p>
            </div>
            {nearbyVehicles.data && nearbyVehicles.data.length > 0 && (
              <div className="mt-3 space-y-2">
                {nearbyVehicles.data.slice(0, 4).map((vehicle) => (
                  <div key={`${vehicle.driver_id}-${vehicle.vehicle_id}`} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm">
                    <span className="capitalize text-slate-700">{vehicle.vehicle_type}</span>
                    <span className="font-semibold text-slate-950">{vehicle.eta_minutes} min</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {bookedRide && (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-5">
              <div className="flex items-center gap-2 text-slate-950">
                <CheckCircle2 size={20} />
                <h2 className="text-sm font-semibold">Ride booked</h2>
              </div>
              <dl className="mt-4 space-y-3 text-sm">
                <Info label="Ride ID" value={bookedRide.id} />
                <Info label="Status" value={bookedRide.status} />
                <Info label="Vehicle" value={bookedRide.ride_type} />
                <Info
                  label="Driver"
                  value={bookedRide.driver_id ? "Assigned" : "Waiting for assignment"}
                />
              </dl>
              <Link to={`/rides/${bookedRide.id}/tracking`} className="mt-4 flex h-10 items-center justify-center rounded-md bg-black text-sm font-semibold text-white">
                Track ride
              </Link>
            </div>
          )}
        </aside>
      </main>
    </MainLayout>
  );
}

function LocationPanel({
  title,
  icon,
  action,
  addressInput,
  addressError,
}: {
  title: string;
  icon: React.ReactNode;
  action?: React.ReactNode;
  addressInput: React.ReactNode;
  addressError?: string;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
          <span className="text-slate-950">{icon}</span>
          {title}
        </div>
        {action}
      </div>
      <div className="space-y-2">
        {addressInput}
        {addressError && <p className="text-xs leading-5 text-red-600">{addressError}</p>}
      </div>
    </div>
  );
}

function locationErrorMessage(error: GeolocationPositionError): string {
  if (error.code === error.PERMISSION_DENIED) {
    return "Location permission was denied. Allow location access or type your Bengaluru pickup.";
  }
  if (error.code === error.POSITION_UNAVAILABLE) {
    return "Current location is unavailable. Type your Bengaluru pickup instead.";
  }
  if (error.code === error.TIMEOUT) {
    return "Location request timed out. Try again or type your Bengaluru pickup.";
  }
  return "Unable to get current location.";
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="break-all font-medium capitalize text-slate-950">{value}</dd>
    </div>
  );
}
