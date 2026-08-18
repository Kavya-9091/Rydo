import { LogOut } from "lucide-react";

import { useAuthStore } from "../features/auth/authStore";

export function AppPlaceholder() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <main className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto flex max-w-5xl items-center justify-between rounded-md border border-slate-200 bg-white p-5">
        <div>
          <p className="text-sm text-slate-500">Signed in as</p>
          <h1 className="text-xl font-semibold text-slate-950">{user?.full_name}</h1>
        </div>
        <button
          className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50"
          onClick={logout}
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </main>
  );
}
