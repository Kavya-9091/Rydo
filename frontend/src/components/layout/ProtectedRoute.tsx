import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "../../features/auth/authStore";

export function ProtectedRoute() {
  const location = useLocation();
  const accessToken = useAuthStore((state) => state.accessToken);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);

  if (!hasHydrated) {
    return null;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
