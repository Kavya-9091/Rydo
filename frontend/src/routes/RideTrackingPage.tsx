import { useMutation, useQuery } from "@tanstack/react-query";
import { CarFront, Circle, MapPin, Navigation, Phone, Star, X } from "lucide-react";
import { useParams } from "react-router-dom";

import { MainLayout } from "../components/layout/MainLayout";
import { cancelRide, getRide } from "../features/rides/rideApi";
import { usePageTitle } from "../lib/usePageTitle";

const steps = ["requested", "accepted", "in_progress", "completed"];

export function RideTrackingPage() {
  usePageTitle("Ride Tracking");
  const { rideId = "" } = useParams();
  const query = useQuery({ queryKey: ["ride", rideId], queryFn: () => getRide(rideId), enabled: Boolean(rideId), refetchInterval: 5000 });
  const cancel = useMutation({ mutationFn: () => cancelRide(rideId, "Cancelled from app"), onSuccess: () => query.refetch() });
  const ride = query.data;

  return (
    <MainLayout>
      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[1fr_380px]">
        <section className="relative min-h-[520px] overflow-hidden rounded-md border border-slate-200 bg-slate-900">
          <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(#ffffff22_1px,transparent_1px),linear-gradient(90deg,#ffffff22_1px,transparent_1px)] [background-size:44px_44px]" />
          <div className="absolute left-[18%] top-[24%] flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm shadow-panel"><MapPin size={16} className="text-slate-950" />Pickup</div>
          <div className="absolute bottom-[24%] right-[18%] flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm shadow-panel"><Navigation size={16} className="text-slate-950" />Destination</div>
          <div className="absolute left-1/2 top-1/2 flex size-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black text-white shadow-panel"><CarFront /></div>
        </section>
        <aside className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-2xl font-semibold text-slate-950">Ride tracking</h1>
          {query.isLoading && <p className="mt-4 text-slate-500">Loading ride...</p>}
          {query.error && (
            <p className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {query.error.message}
            </p>
          )}
          {!query.error && ride && (
            <>
              <p className="mt-2 text-sm capitalize text-slate-500">{ride.status}</p>
              <div className="mt-6 space-y-4">
                {steps.map((step) => {
                  const active = steps.indexOf(ride.status) >= steps.indexOf(step);
                  return <div key={step} className="flex items-center gap-3 text-sm"><Circle size={14} className={active ? "fill-black text-black" : "text-slate-300"} /><span className="capitalize">{step.replace("_", " ")}</span></div>;
                })}
              </div>
              <div className="mt-6 space-y-3 rounded-md bg-slate-50 p-4 text-sm">
                <p><strong>From:</strong> {ride.pickup_address}</p>
                <p><strong>To:</strong> {ride.dropoff_address}</p>
                <p><strong>Fare:</strong> {ride.currency} {ride.estimated_fare ?? "--"}</p>
              </div>
              {ride.driver_details && ride.vehicle_details && (
                <div className="mt-4 rounded-md border border-slate-200 bg-white p-4 text-sm">
                  <p className="font-semibold text-slate-950">Driver assigned</p>
                  <div className="mt-3 space-y-2 text-slate-700">
                    <p><strong>Driver:</strong> {ride.driver_details.full_name}</p>
                    <p className="flex items-center gap-2">
                      <Phone size={15} />
                      <a className="font-semibold text-slate-950" href={`tel:${ride.driver_details.phone_number}`}>
                        {ride.driver_details.phone_number}
                      </a>
                    </p>
                    <p className="flex items-center gap-2">
                      <Star size={15} />
                      {ride.driver_details.average_rating ?? "New"} rating · {ride.driver_details.total_rides} rides
                    </p>
                    <p>
                      <strong>Vehicle:</strong> {ride.vehicle_details.color} {ride.vehicle_details.make} {ride.vehicle_details.model}
                    </p>
                    <p><strong>Number:</strong> {ride.vehicle_details.registration_number}</p>
                  </div>
                </div>
              )}
              {!["completed", "cancelled"].includes(ride.status) && (
                <button onClick={() => cancel.mutate()} className="mt-5 flex h-11 w-full items-center justify-center gap-2 rounded-md border border-red-200 text-sm font-semibold text-red-700 hover:bg-red-50"><X size={16} /> Cancel ride</button>
              )}
            </>
          )}
        </aside>
      </main>
    </MainLayout>
  );
}
