import { useQuery } from "@tanstack/react-query";
import { Clock3, MapPin, Navigation } from "lucide-react";
import { Link } from "react-router-dom";

import { MainLayout } from "../components/layout/MainLayout";
import { getRideHistory } from "../features/rides/rideApi";
import { usePageTitle } from "../lib/usePageTitle";

export function RideHistoryPage() {
  usePageTitle("Ride History");
  const { data, isLoading, error } = useQuery({ queryKey: ["ride-history"], queryFn: getRideHistory });

  return (
    <MainLayout>
      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <h1 className="text-3xl font-semibold text-slate-950">Ride history</h1>
        <div className="mt-5 space-y-3">
          {isLoading && <div className="rounded-md bg-white p-5 text-slate-500">Loading rides...</div>}
          {error && <div className="rounded-md bg-red-50 p-5 text-red-700">{error.message}</div>}
          {data?.map((ride) => (
            <Link key={ride.id} to={`/rides/${ride.id}/tracking`} className="block rounded-md border border-slate-200 bg-white p-4 hover:border-slate-400">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2">
                  <p className="flex items-center gap-2 font-semibold text-slate-950"><MapPin size={16} />{ride.pickup_address}</p>
                  <p className="flex items-center gap-2 text-sm text-slate-600"><Navigation size={16} />{ride.dropoff_address}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold capitalize text-slate-950">{ride.status}</p>
                  <p className="flex items-center gap-1 text-xs text-slate-500"><Clock3 size={13} />{new Date(ride.requested_at).toLocaleString()}</p>
                </div>
              </div>
            </Link>
          ))}
          {data?.length === 0 && <div className="rounded-md bg-white p-5 text-slate-500">No rides yet.</div>}
        </div>
      </main>
    </MainLayout>
  );
}
