import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Loader2 } from "lucide-react";

import { MainLayout } from "../components/layout/MainLayout";
import { getNotifications, markNotificationRead } from "../features/rides/rideApi";
import { usePageTitle } from "../lib/usePageTitle";

export function NotificationsPage() {
  usePageTitle("Notifications");
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["notifications"], queryFn: getNotifications, refetchInterval: 10000 });
  const markRead = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <MainLayout>
      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-slate-950">Notifications</h1>
              <p className="mt-2 text-sm text-slate-500">Ride, payment, and account updates.</p>
            </div>
            {query.isFetching && <Loader2 size={20} className="animate-spin text-slate-400" />}
          </div>

          <div className="mt-6 space-y-3">
            {query.data?.length === 0 && <p className="rounded-md bg-slate-50 p-4 text-sm text-slate-500">No notifications yet.</p>}
            {query.data?.map((notification) => (
              <div key={notification.id} className={`rounded-md border p-4 ${notification.is_read ? "border-slate-200 bg-white" : "border-black bg-slate-50"}`}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex gap-3">
                    <span className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-md bg-black text-white">
                      <Bell size={17} />
                    </span>
                    <div>
                      <p className="font-semibold text-slate-950">{notification.title}</p>
                      <p className="mt-1 text-sm text-slate-600">{notification.message}</p>
                      <p className="mt-2 text-xs capitalize text-slate-400">{notification.notification_type.replace("_", " ")}</p>
                    </div>
                  </div>
                  {!notification.is_read && (
                    <button
                      type="button"
                      onClick={() => markRead.mutate(notification.id)}
                      className="rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-white"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            ))}
            {query.error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{query.error.message}</p>}
          </div>
        </section>
      </main>
    </MainLayout>
  );
}
