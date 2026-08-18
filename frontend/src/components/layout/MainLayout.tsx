import { Bell, CarTaxiFront, Clock3, CreditCard, Gauge, History, LogOut, Settings, Star, UserRound } from "lucide-react";
import { NavLink } from "react-router-dom";

import { AIChatAssistant } from "../ai/AIChatAssistant";
import { useAuthStore } from "../../features/auth/authStore";

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-md bg-ink text-white">
              <CarTaxiFront size={22} />
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-950">Rydo</p>
              <p className="text-xs text-slate-500">City rides, cleanly managed</p>
            </div>
          </div>

          <nav className="hidden items-center gap-1 md:flex">
            {user?.role === "driver" ? (
              <NavItem to="/driver" icon={<Gauge size={16} />} label="Drive" />
            ) : user?.role === "admin" ? (
              <NavItem to="/admin" icon={<Gauge size={16} />} label="Admin" />
            ) : (
              <NavItem to="/app" icon={<Clock3 size={16} />} label="Book" />
            )}
            {user?.role === "customer" && <NavItem to="/history" icon={<History size={16} />} label="History" />}
            {user?.role === "customer" && <NavItem to="/payment" icon={<CreditCard size={16} />} label="Payment" />}
            {user?.role === "customer" && <NavItem to="/ratings" icon={<Star size={16} />} label="Ratings" />}
            <NavItem to="/notifications" icon={<Bell size={16} />} label="Alerts" />
            <NavItem to="/profile" icon={<UserRound size={16} />} label="Profile" />
            <NavItem to="/settings" icon={<Settings size={16} />} label="Settings" />
          </nav>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-slate-950">{user?.full_name}</p>
              <p className="text-xs capitalize text-slate-500">{user?.role}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="flex h-10 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-50"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      {children}
      <AIChatAssistant />
    </div>
  );
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
          isActive ? "bg-slate-100 text-slate-950" : "text-slate-500 hover:bg-slate-50"
        }`
      }
    >
      {icon}
      {label}
    </NavLink>
  );
}
