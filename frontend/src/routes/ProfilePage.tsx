import { Mail, Phone, ShieldCheck, UserRound } from "lucide-react";

import { MainLayout } from "../components/layout/MainLayout";
import { useAuthStore } from "../features/auth/authStore";
import { usePageTitle } from "../lib/usePageTitle";

export function ProfilePage() {
  usePageTitle("Profile");
  const user = useAuthStore((state) => state.user);
  return (
    <MainLayout>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="flex size-16 items-center justify-center rounded-md bg-slate-950 text-white"><UserRound /></div>
            <div>
              <h1 className="text-3xl font-semibold text-slate-950">{user?.full_name}</h1>
              <p className="capitalize text-slate-500">{user?.role}</p>
            </div>
          </div>
          <div className="mt-6 grid gap-3">
            <Info icon={<Mail size={18} />} label="Email" value={user?.email ?? ""} />
            <Info icon={<Phone size={18} />} label="Phone" value={user?.phone_number ?? ""} />
            <Info icon={<ShieldCheck size={18} />} label="Status" value={user?.status ?? ""} />
          </div>
        </section>
      </main>
    </MainLayout>
  );
}

function Info({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="flex items-center gap-3 rounded-md bg-slate-50 p-4"><span className="text-slate-950">{icon}</span><div><p className="text-xs text-slate-500">{label}</p><p className="font-medium text-slate-950">{value}</p></div></div>;
}
