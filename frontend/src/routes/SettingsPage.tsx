import { Bell, MapPin, ShieldCheck } from "lucide-react";

import { MainLayout } from "../components/layout/MainLayout";
import { usePageTitle } from "../lib/usePageTitle";

export function SettingsPage() {
  usePageTitle("Settings");

  return (
    <MainLayout>
      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-3xl font-semibold text-slate-950">Settings</h1>
          <p className="mt-2 text-sm text-slate-500">Manage app preferences for the current session.</p>

          <div className="mt-6 grid gap-4">
            <SettingRow icon={<Bell size={20} />} title="Ride notifications" description="Show ride, payment, and driver updates inside Rydo." enabled />
            <SettingRow icon={<MapPin size={20} />} title="Location access" description="Use browser location for pickup and driver availability." enabled />
            <SettingRow icon={<ShieldCheck size={20} />} title="Secure session" description="Keep each browser tab signed in separately for role testing." enabled />
          </div>
        </section>
      </main>
    </MainLayout>
  );
}

function SettingRow({ icon, title, description, enabled }: { icon: React.ReactNode; title: string; description: string; enabled: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="flex gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-white text-slate-950">{icon}</span>
        <div>
          <p className="font-semibold text-slate-950">{title}</p>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
      </div>
      <span className={`h-6 w-11 rounded-full p-1 ${enabled ? "bg-black" : "bg-slate-300"}`}>
        <span className={`block size-4 rounded-full bg-white ${enabled ? "translate-x-5" : ""}`} />
      </span>
    </div>
  );
}
