import { Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "../components/layout/ProtectedRoute";
import { RoleRoute } from "../components/layout/RoleRoute";
import { AuthPage } from "../routes/AuthPage";
import { AdminDashboardPage } from "../routes/AdminDashboardPage";
import { DriverDashboardPage } from "../routes/DriverDashboardPage";
import { HomePage } from "../routes/HomePage";
import { LandingPage } from "../routes/LandingPage";
import { PaymentPage } from "../routes/PaymentPage";
import { ProfilePage } from "../routes/ProfilePage";
import { NotificationsPage } from "../routes/NotificationsPage";
import { RatingsPage } from "../routes/RatingsPage";
import { RentPage } from "../routes/RentPage";
import { RideHistoryPage } from "../routes/RideHistoryPage";
import { RideTrackingPage } from "../routes/RideTrackingPage";
import { SettingsPage } from "../routes/SettingsPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/rent" element={<RentPage />} />
      <Route path="/:mode" element={<AuthPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<RoleRoute allow={["customer"]} />}>
          <Route path="/app" element={<HomePage />} />
          <Route path="/history" element={<RideHistoryPage />} />
          <Route path="/rides/:rideId/tracking" element={<RideTrackingPage />} />
          <Route path="/payment" element={<PaymentPage />} />
          <Route path="/ratings" element={<RatingsPage />} />
        </Route>
        <Route element={<RoleRoute allow={["driver"]} />}>
          <Route path="/driver" element={<DriverDashboardPage />} />
        </Route>
        <Route element={<RoleRoute allow={["admin"]} />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
        </Route>
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

