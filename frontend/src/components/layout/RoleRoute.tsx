import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "../../features/auth/authStore";
import type { UserRole } from "../../types/auth";

const DEFAULT_ROUTE_BY_ROLE: Record<UserRole, string> = {
  customer: "/app",
  driver: "/driver",
  admin: "/admin",
};

interface RoleRouteProps {
  allow: UserRole[];
}

export function RoleRoute({ allow }: RoleRouteProps) {
  const user = useAuthStore((state) => state.user);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);

  if (!hasHydrated) {
    return null;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allow.includes(user.role)) {
    return <Navigate to={DEFAULT_ROUTE_BY_ROLE[user.role]} replace />;
  }

  return <Outlet />;
}
