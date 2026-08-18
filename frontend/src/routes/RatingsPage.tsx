import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Star } from "lucide-react";
import { useState } from "react";

import { MainLayout } from "../components/layout/MainLayout";
import { getRideHistory, rateRide } from "../features/rides/rideApi";
import { usePageTitle } from "../lib/usePageTitle";

export function RatingsPage() {
  usePageTitle("Ratings");
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["ride-history"], queryFn: getRideHistory });
  const [selectedRideId, setSelectedRideId] = useState<string | null>(null);
  const [score, setScore] = useState(5);
  const [comment, setComment] = useState("");
  const completedRides = data?.filter((ride) => ride.status === "completed") ?? [];
  const selectedRide = completedRides.find((ride) => ride.id === selectedRideId) ?? completedRides[0];
  const mutation = useMutation({
    mutationFn: () => rateRide(selectedRide!.id, score, comment),
    onSuccess: () => {
      setComment("");
      queryClient.invalidateQueries({ queryKey: ["ride-history"] });
    },
  });

  return (
    <MainLayout>
      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-3xl font-semibold text-slate-950">Ratings</h1>
          <p className="mt-2 text-sm text-slate-500">Rate completed rides and help keep service quality high.</p>

          {isLoading && <p className="mt-6 text-sm text-slate-500">Loading completed rides...</p>}
          {!isLoading && completedRides.length === 0 && (
            <p className="mt-6 rounded-md bg-slate-50 p-4 text-sm text-slate-500">No completed rides available for rating.</p>
          )}

          {selectedRide && (
            <div className="mt-6 grid gap-5">
              <select
                value={selectedRide.id}
                onChange={(event) => setSelectedRideId(event.target.value)}
                className="h-12 rounded-md border border-slate-200 px-3 text-sm"
              >
                {completedRides.map((ride) => (
                  <option key={ride.id} value={ride.id}>
                    {ride.pickup_address} to {ride.dropoff_address}
                  </option>
                ))}
              </select>

              <div className="rounded-md bg-slate-50 p-4 text-sm">
                <p><strong>From:</strong> {selectedRide.pickup_address}</p>
                <p className="mt-2"><strong>To:</strong> {selectedRide.dropoff_address}</p>
              </div>

              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setScore(value)}
                    className={`flex size-11 items-center justify-center rounded-md border ${
                      value <= score ? "border-black bg-black text-white" : "border-slate-200 bg-white text-slate-400"
                    }`}
                    aria-label={`${value} star rating`}
                  >
                    <Star size={18} className={value <= score ? "fill-white" : ""} />
                  </button>
                ))}
              </div>

              <textarea
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                maxLength={1000}
                rows={4}
                placeholder="Tell us about the ride"
                className="rounded-md border border-slate-200 px-3 py-3 text-sm outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10"
              />

              <button
                type="button"
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
                className="flex h-12 items-center justify-center gap-2 rounded-md bg-black text-sm font-semibold text-white disabled:opacity-60"
              >
                {mutation.isPending && <Loader2 size={18} className="animate-spin" />}
                Submit rating
              </button>
              {mutation.data && <p className="rounded-md bg-slate-100 p-3 text-sm text-slate-900">Rating submitted.</p>}
              {mutation.error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{mutation.error.message}</p>}
            </div>
          )}
        </section>
      </main>
    </MainLayout>
  );
}
