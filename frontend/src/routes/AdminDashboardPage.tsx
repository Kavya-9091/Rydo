import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, ShieldCheck, UsersRound } from "lucide-react";
import { useState } from "react";

import { MainLayout } from "../components/layout/MainLayout";
import { approveDriver, approveVehicle, listDrivers, listUsers, listVehicles } from "../features/drivers/driverApi";
import { usePageTitle } from "../lib/usePageTitle";

export function AdminDashboardPage() {
  usePageTitle("Admin Dashboard");
  const queryClient = useQueryClient();
  const [activeSection, setActiveSection] = useState<"users" | "approvals">("approvals");
  const users = useQuery({ queryKey: ["admin-users"], queryFn: listUsers });
  const drivers = useQuery({ queryKey: ["admin-drivers"], queryFn: listDrivers });
  const vehicles = useQuery({ queryKey: ["admin-vehicles"], queryFn: listVehicles });
  const approveDriverMutation = useMutation({
    mutationFn: approveDriver,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-drivers"] }),
  });
  const approveVehicleMutation = useMutation({
    mutationFn: approveVehicle,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-vehicles"] }),
  });

  return (
    <MainLayout>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Admin</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">Operations dashboard</h1>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <button
              type="button"
              onClick={() => setActiveSection("users")}
              className={`rounded-md border p-4 text-left transition ${
                activeSection === "users"
                  ? "border-black bg-white shadow-sm"
                  : "border-slate-200 bg-slate-50 hover:bg-white"
              }`}
            >
              <UsersRound className="text-slate-950" size={22} />
              <h2 className="mt-3 font-semibold text-slate-950">Users</h2>
              <p className="mt-1 text-sm text-slate-500">{users.data?.length ?? 0} registered accounts across customers, drivers, and admins.</p>
            </button>
            <button
              type="button"
              onClick={() => setActiveSection("approvals")}
              className={`rounded-md border p-4 text-left transition ${
                activeSection === "approvals"
                  ? "border-black bg-white shadow-sm"
                  : "border-slate-200 bg-slate-50 hover:bg-white"
              }`}
            >
              <ShieldCheck className="text-slate-950" size={22} />
              <h2 className="mt-3 font-semibold text-slate-950">Approvals</h2>
              <p className="mt-1 text-sm text-slate-500">Approve drivers and vehicles before they go online.</p>
            </button>
          </div>

          {activeSection === "users" && <section className="mt-6 rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold text-slate-950">Registered users</h2>
              {users.isFetching && <Loader2 size={16} className="animate-spin text-slate-400" />}
            </div>
            <div className="mt-4 overflow-hidden rounded-md border border-slate-200">
              <div className="grid grid-cols-[1.2fr_1.4fr_1fr_0.8fr_0.8fr] gap-3 bg-slate-50 px-3 py-2 text-xs font-semibold uppercase text-slate-500">
                <span>Name</span>
                <span>Email</span>
                <span>Phone</span>
                <span>Role</span>
                <span>Status</span>
              </div>
              {users.data?.length === 0 && <p className="px-3 py-4 text-sm text-slate-500">No users registered yet.</p>}
              {users.data?.map((user) => (
                <div key={user.id} className="grid grid-cols-[1.2fr_1.4fr_1fr_0.8fr_0.8fr] gap-3 border-t border-slate-200 px-3 py-3 text-sm">
                  <span className="min-w-0 truncate font-medium text-slate-950">{user.full_name}</span>
                  <span className="min-w-0 truncate text-slate-600">{user.email}</span>
                  <span className="text-slate-600">{user.phone_number}</span>
                  <span className="capitalize text-slate-600">{user.role}</span>
                  <span className="capitalize text-slate-600">{user.status.replace("_", " ")}</span>
                </div>
              ))}
            </div>
          </section>}

          {activeSection === "approvals" && <div className="mt-6 grid gap-5 lg:grid-cols-2">
            <section className="rounded-md border border-slate-200 bg-white p-4">
              <h2 className="font-semibold text-slate-950">Driver approvals</h2>
              <div className="mt-4 space-y-3">
                {drivers.isLoading && <p className="text-sm text-slate-500">Loading drivers...</p>}
                {drivers.data?.map((driver) => (
                  <div key={driver.id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                    <p className="break-all text-sm font-medium text-slate-950">{driver.id}</p>
                    <p className="mt-1 text-sm capitalize text-slate-600">Status: {driver.approval_status}</p>
                    {driver.approval_status !== "approved" && (
                      <button
                        onClick={() => approveDriverMutation.mutate(driver.id)}
                        className="mt-3 flex h-9 items-center gap-2 rounded-md bg-black px-3 text-sm font-semibold text-white"
                      >
                        {approveDriverMutation.isPending && <Loader2 size={14} className="animate-spin" />}
                        Approve driver
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-4">
              <h2 className="font-semibold text-slate-950">Vehicle approvals</h2>
              <div className="mt-4 space-y-3">
                {vehicles.isLoading && <p className="text-sm text-slate-500">Loading vehicles...</p>}
                {vehicles.data?.map((vehicle) => (
                  <div key={vehicle.id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                    <p className="text-sm font-medium text-slate-950">{vehicle.make} {vehicle.model}</p>
                    <p className="mt-1 text-sm text-slate-600">{vehicle.registration_number} · {vehicle.vehicle_type}</p>
                    <p className="mt-1 text-sm capitalize text-slate-600">Status: {vehicle.approval_status}</p>
                    {vehicle.approval_status !== "approved" && (
                      <button
                        onClick={() => approveVehicleMutation.mutate(vehicle.id)}
                        className="mt-3 flex h-9 items-center gap-2 rounded-md bg-black px-3 text-sm font-semibold text-white"
                      >
                        {approveVehicleMutation.isPending && <Loader2 size={14} className="animate-spin" />}
                        Approve vehicle
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </div>}
        </section>
      </main>
    </MainLayout>
  );
}
