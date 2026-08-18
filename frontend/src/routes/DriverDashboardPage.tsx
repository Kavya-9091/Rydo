import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CarFront, CirclePower, Clock3, Loader2, MapPin, Navigation } from "lucide-react";
import { useState } from "react";

import { MainLayout } from "../components/layout/MainLayout";
import { getDriverProfile, goOffline, goOnline, listAssignedRides, registerDriver, registerVehicle, type VehiclePayload } from "../features/drivers/driverApi";
import { acceptRide, completeRide, rejectRide, startRide } from "../features/rides/rideApi";
import { usePageTitle } from "../lib/usePageTitle";

type VehicleCatalogEntry = {
  makes: Record<string, string[]>;
  capacity: number;
};

const vehicleCatalog: Record<VehiclePayload["vehicle_type"], VehicleCatalogEntry> = {
  bike: {
    makes: {
      Honda: ["Activa", "Dio", "Shine"],
      TVS: ["Jupiter", "Raider", "Apache"],
      Bajaj: ["Pulsar", "Chetak", "Platina"],
      Hero: ["Splendor", "Passion", "Maestro"],
    },
    capacity: 1,
  },
  auto: {
    makes: {
      Bajaj: ["RE", "Compact RE"],
      Piaggio: ["Ape Auto", "Ape City"],
      TVS: ["King Deluxe", "King Duramax"],
    },
    capacity: 3,
  },
  mini: {
    makes: {
      Maruti: ["Swift", "WagonR", "Celerio"],
      Hyundai: ["Grand i10", "i20"],
      Tata: ["Tiago", "Punch"],
    },
    capacity: 4,
  },
  sedan: {
    makes: {
      Honda: ["Amaze", "City"],
      Hyundai: ["Aura", "Verna"],
      Maruti: ["Dzire", "Ciaz"],
      Toyota: ["Etios", "Yaris"],
    },
    capacity: 4,
  },
  suv: {
    makes: {
      Hyundai: ["Creta", "Venue"],
      Tata: ["Nexon", "Harrier"],
      Mahindra: ["XUV300", "Scorpio", "XUV700"],
      Toyota: ["Innova Crysta", "Urban Cruiser"],
    },
    capacity: 6,
  },
  luxury: {
    makes: {
      Mercedes: ["E-Class", "C-Class"],
      BMW: ["3 Series", "5 Series"],
      Audi: ["A4", "A6"],
      Toyota: ["Camry"],
    },
    capacity: 4,
  },
};

const vehicleColors = ["White", "Black", "Silver", "Grey", "Blue", "Red", "Brown"];

export function DriverDashboardPage() {
  usePageTitle("Driver Dashboard");
  const queryClient = useQueryClient();
  const defaultVehicleType: VehiclePayload["vehicle_type"] = "sedan";
  const defaultMake = Object.keys(vehicleCatalog[defaultVehicleType].makes)[0];
  const [vehicle, setVehicle] = useState<VehiclePayload>({
    vehicle_type: defaultVehicleType,
    make: defaultMake,
    model: vehicleCatalog[defaultVehicleType].makes[defaultMake][0],
    color: vehicleColors[0],
    registration_number: "",
    capacity: vehicleCatalog[defaultVehicleType].capacity,
  });
  const [vehicleFormError, setVehicleFormError] = useState<string | null>(null);
  const driverProfile = useQuery({
    queryKey: ["driver-profile"],
    queryFn: getDriverProfile,
    retry: false,
  });
  const refreshDriver = () => {
    queryClient.invalidateQueries({ queryKey: ["driver-profile"] });
    queryClient.invalidateQueries({ queryKey: ["driver-rides"] });
  };
  const register = useMutation({ mutationFn: registerDriver, onSuccess: refreshDriver });
  const vehicleMutation = useMutation({ mutationFn: registerVehicle, onSuccess: refreshDriver });
  const assignedRides = useQuery({
    queryKey: ["driver-rides"],
    queryFn: listAssignedRides,
    refetchInterval: 5000,
  });
  const refreshDriverRides = () => {
    queryClient.invalidateQueries({ queryKey: ["driver-rides"] });
    queryClient.invalidateQueries({ queryKey: ["driver-profile"] });
  };
  const acceptMutation = useMutation({ mutationFn: acceptRide, onSuccess: refreshDriverRides });
  const startMutation = useMutation({ mutationFn: startRide, onSuccess: refreshDriverRides });
  const completeMutation = useMutation({ mutationFn: completeRide, onSuccess: refreshDriverRides });
  const rejectMutation = useMutation({ mutationFn: rejectRide, onSuccess: refreshDriverRides });
  const online = useMutation({
    mutationFn: () =>
      new Promise<{ latitude: number; longitude: number }>((resolve, reject) =>
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
          reject,
        ),
      ).then((coords) => goOnline(coords.latitude, coords.longitude)),
    onSuccess: refreshDriver,
  });
  const offline = useMutation({ mutationFn: goOffline, onSuccess: refreshDriver });
  const profile = driverProfile.data ?? register.data ?? online.data ?? offline.data;
  const hasProfile = Boolean(profile);
  const isApproved = profile?.approval_status === "approved";
  const isBusy = profile?.availability_status === "busy";
  const makeOptions = Object.keys(vehicleCatalog[vehicle.vehicle_type].makes);
  const modelOptions = vehicleCatalog[vehicle.vehicle_type].makes[vehicle.make] ?? [];

  function updateVehicleType(vehicleType: VehiclePayload["vehicle_type"]) {
    const make = Object.keys(vehicleCatalog[vehicleType].makes)[0];
    setVehicle({
      ...vehicle,
      vehicle_type: vehicleType,
      make,
      model: vehicleCatalog[vehicleType].makes[make][0],
      capacity: vehicleCatalog[vehicleType].capacity,
    });
  }

  function submitVehicle() {
    const registrationNumber = vehicle.registration_number.trim().toUpperCase();
    if (!/^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$/.test(registrationNumber)) {
      setVehicleFormError("Enter a valid registration number, for example KA07AB1234.");
      return;
    }
    setVehicleFormError(null);
    vehicleMutation.mutate({ ...vehicle, registration_number: registrationNumber });
  }

  return (
    <MainLayout>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Driver dashboard</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">Manage your ride availability</h1>
          <div className="mt-6 flex flex-wrap gap-3">
            {!hasProfile && (
              <button
                onClick={() => register.mutate()}
                disabled={register.isPending}
                className="flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              >
                {register.isPending && <Loader2 size={16} className="animate-spin" />}
                Create driver profile
              </button>
            )}
            <button
              onClick={() => online.mutate()}
              disabled={!isApproved || online.isPending || isBusy}
              title={!isApproved ? "Admin approval is required before going online" : isBusy ? "Complete or reject the active ride before going online again" : "Go online"}
              className="flex items-center gap-2 rounded-md bg-black px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {online.isPending && <Loader2 size={16} className="animate-spin" />}
              Go online
            </button>
            <button
              onClick={() => offline.mutate()}
              disabled={!hasProfile || offline.isPending}
              className="flex items-center gap-2 rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            >
              {offline.isPending && <Loader2 size={16} className="animate-spin" />}
              Go offline
            </button>
          </div>
          {profile && <p className="mt-4 rounded-md bg-slate-100 p-3 text-sm text-slate-900">Driver is {profile.availability_status}.</p>}
          {(register.error || vehicleMutation.error || online.error || offline.error || acceptMutation.error || startMutation.error || completeMutation.error || rejectMutation.error) && (
            <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
              {(register.error || vehicleMutation.error || online.error || offline.error || acceptMutation.error || startMutation.error || completeMutation.error || rejectMutation.error)?.message}
            </p>
          )}
          {profile && (
            <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm">
              <p className="font-semibold text-slate-950">Driver profile</p>
              <p className="mt-1 text-slate-600">Availability: <span className="font-semibold capitalize">{profile.availability_status}</span></p>
              {!isApproved && <p className="mt-1 text-slate-500">Admin must approve this driver before going online.</p>}
              {isBusy && <p className="mt-1 text-slate-500">You are busy with an accepted ride. Complete or reject it before taking another ride.</p>}
            </div>
          )}
          <form
            className="mt-6 rounded-md border border-slate-200 bg-white p-4"
            onSubmit={(event) => {
              event.preventDefault();
              submitVehicle();
            }}
          >
            <h2 className="font-semibold text-slate-950">Register vehicle</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <select value={vehicle.vehicle_type} onChange={(event) => updateVehicleType(event.target.value as VehiclePayload["vehicle_type"])} className="h-11 rounded-md border border-slate-200 px-3">
                <option value="bike">Bike</option>
                <option value="auto">Auto</option>
                <option value="mini">Mini</option>
                <option value="sedan">Sedan</option>
                <option value="suv">SUV</option>
                <option value="luxury">Luxury</option>
              </select>
              <select
                value={vehicle.make}
                onChange={(event) => {
                  const make = event.target.value;
                  setVehicle({ ...vehicle, make, model: vehicleCatalog[vehicle.vehicle_type].makes[make][0] });
                }}
                className="h-11 rounded-md border border-slate-200 px-3"
              >
                {makeOptions.map((make) => <option key={make} value={make}>{make}</option>)}
              </select>
              <select value={vehicle.model} onChange={(event) => setVehicle({ ...vehicle, model: event.target.value })} className="h-11 rounded-md border border-slate-200 px-3">
                {modelOptions.map((model) => <option key={model} value={model}>{model}</option>)}
              </select>
              <select value={vehicle.color} onChange={(event) => setVehicle({ ...vehicle, color: event.target.value })} className="h-11 rounded-md border border-slate-200 px-3">
                {vehicleColors.map((color) => <option key={color} value={color}>{color}</option>)}
              </select>
              <input value={vehicle.registration_number} onChange={(event) => setVehicle({ ...vehicle, registration_number: event.target.value.toUpperCase() })} placeholder="Registration number" className="h-11 rounded-md border border-slate-200 px-3" />
              <input value={vehicle.capacity} onChange={(event) => setVehicle({ ...vehicle, capacity: Number(event.target.value) })} type="number" min={1} max={12} placeholder="Capacity" className="h-11 rounded-md border border-slate-200 px-3" />
            </div>
            {vehicleFormError && <p className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{vehicleFormError}</p>}
            <button disabled={vehicleMutation.isPending} className="mt-4 flex h-11 items-center gap-2 rounded-md bg-black px-4 text-sm font-semibold text-white">
              {vehicleMutation.isPending && <Loader2 size={16} className="animate-spin" />}
              Submit vehicle for approval
            </button>
            {vehicleMutation.data && <p className="mt-3 rounded-md bg-slate-100 p-3 text-sm text-slate-900">Vehicle submitted. Approval status: {vehicleMutation.data.approval_status}</p>}
          </form>
          <section className="mt-6 rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-slate-950">Ride requests</h2>
                <p className="mt-1 text-sm text-slate-500">Accept assigned trips, start pickup, and complete the ride.</p>
              </div>
              {assignedRides.isFetching && <Loader2 size={18} className="animate-spin text-slate-400" />}
            </div>
            <div className="mt-4 space-y-3">
              {assignedRides.data?.length === 0 && (
                <p className="rounded-md bg-slate-50 p-4 text-sm text-slate-500">No assigned ride requests yet. Go online and book a matching ride from a customer account.</p>
              )}
              {assignedRides.data?.map((ride) => (
                <div key={ride.id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold capitalize text-slate-950">{ride.status.replace("_", " ")}</p>
                      <p className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                        <Clock3 size={15} />
                        Requested {formatRideRequestTime(ride.requested_at)} ({formatTimeAgo(ride.requested_at)})
                      </p>
                      <p className="mt-2 text-sm text-slate-700"><span className="font-semibold">Pickup:</span> {ride.pickup_address}</p>
                      <p className="mt-1 text-sm text-slate-700"><span className="font-semibold">Drop:</span> {ride.dropoff_address}</p>
                      <p className="mt-2 text-sm font-semibold text-slate-950">Fare: INR {ride.estimated_fare ?? "--"}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {ride.status === "requested" && (
                        <button
                          type="button"
                          onClick={() => acceptMutation.mutate(ride.id)}
                          disabled={acceptMutation.isPending}
                          className="rounded-md bg-black px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                        >
                          Accept
                        </button>
                      )}
                      {["requested", "accepted"].includes(ride.status) && (
                        <button
                          type="button"
                          onClick={() => rejectMutation.mutate(ride.id)}
                          disabled={rejectMutation.isPending}
                          className="rounded-md border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-60"
                        >
                          Reject
                        </button>
                      )}
                      {ride.status === "accepted" && (
                        <button
                          type="button"
                          onClick={() => startMutation.mutate(ride.id)}
                          disabled={startMutation.isPending}
                          className="flex items-center gap-2 rounded-md bg-black px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                        >
                          <Navigation size={16} />
                          Start
                        </button>
                      )}
                      {ride.status === "in_progress" && (
                        <button
                          type="button"
                          onClick={() => completeMutation.mutate(ride.id)}
                          disabled={completeMutation.isPending}
                          className="rounded-md bg-black px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                        >
                          Complete
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <CirclePower className="text-slate-950" size={22} />
              <h2 className="mt-3 font-semibold text-slate-950">Go online</h2>
              <p className="mt-1 text-sm text-slate-500">Set your active status and receive nearby ride requests.</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <CarFront className="text-slate-950" size={22} />
              <h2 className="mt-3 font-semibold text-slate-950">Vehicle</h2>
              <p className="mt-1 text-sm text-slate-500">Register and manage your approved vehicle.</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <MapPin className="text-slate-950" size={22} />
              <h2 className="mt-3 font-semibold text-slate-950">Location</h2>
              <p className="mt-1 text-sm text-slate-500">Share current location when going online.</p>
            </div>
          </div>
        </section>
      </main>
    </MainLayout>
  );
}

function formatRideRequestTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatTimeAgo(value: string) {
  const diffMs = Date.now() - new Date(value).getTime();
  const diffMinutes = Math.max(0, Math.floor(diffMs / 60000));
  if (diffMinutes < 1) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hr ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
}
