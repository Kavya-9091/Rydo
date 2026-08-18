import { useMutation } from "@tanstack/react-query";
import { CarTaxiFront, MapPinned, ShieldCheck } from "lucide-react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import { AuthForm } from "../components/auth/AuthForm";
import { login, register } from "../features/auth/authApi";
import { useAuthStore } from "../features/auth/authStore";
import { usePageTitle } from "../lib/usePageTitle";
import type { AuthResponse, LoginPayload, RegisterPayload } from "../types/auth";

export function AuthPage() {
  const { mode = "login" } = useParams<{ mode: "login" | "register" }>();
  const authMode = mode === "register" ? "register" : "login";
  usePageTitle(authMode === "register" ? "Register" : "Login");
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((state) => state.setSession);
  const mutation = useMutation({
    mutationFn: (values: LoginPayload | RegisterPayload) =>
      authMode === "register" ? register(values as RegisterPayload) : login(values as LoginPayload),
    onSuccess: (response: AuthResponse) => {
      setSession(response.user, response.tokens.access_token, response.tokens.refresh_token);
      const route =
        (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ??
        defaultRouteForRole(response.user.role);
      const redirectTo = response.user.role === "customer" && route === "/app" ? `${route}${location.search}` : route;
      navigate(redirectTo, { replace: true });
    },
  });

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="relative hidden overflow-hidden bg-road text-white lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(18,184,134,0.22),transparent_28%),linear-gradient(135deg,#111827,#202124_55%,#0f172a)]" />
          <div className="relative flex h-full flex-col justify-between p-12">
            <div className="flex items-center gap-3 text-lg font-semibold">
              <span className="flex size-10 items-center justify-center rounded-md bg-white text-black">
                <CarTaxiFront size={24} />
              </span>
              Rydo
            </div>

            <div className="max-w-xl">
              <p className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-white/70">
                Ride smarter
              </p>
              <h1 className="text-5xl font-semibold leading-tight">
                Move through your city with clean, reliable rides.
              </h1>
              <div className="mt-8 grid gap-3 text-sm text-slate-200">
                <div className="flex items-center gap-3">
                  <MapPinned size={20} className="text-white" />
                  Live pickup, destination, and ride tracking
                </div>
                <div className="flex items-center gap-3">
                  <ShieldCheck size={20} className="text-white" />
                  Secure login with protected ride workflows
                </div>
              </div>
            </div>

            <div className="h-28 rounded-md border border-white/10 bg-white/5 p-4">
              <div className="mb-4 h-2 w-1/2 rounded bg-white/20" />
              <div className="grid grid-cols-3 gap-3">
                <div className="h-14 rounded bg-white/10" />
                <div className="h-14 rounded bg-white/25" />
                <div className="h-14 rounded bg-white/15" />
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-5 py-10">
          <div className="w-full max-w-md">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <span className="flex size-10 items-center justify-center rounded-md bg-ink text-white">
                <CarTaxiFront size={22} />
              </span>
              <span className="text-lg font-semibold">Rydo</span>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-6 shadow-panel sm:p-8">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-slate-950">
                  {authMode === "register" ? "Create your account" : "Welcome back"}
                </h2>
                <p className="mt-2 text-sm text-slate-500">
                  {authMode === "register"
                    ? "Register as a customer, driver, or admin."
                    : "Sign in to continue your ride workflow."}
                </p>
              </div>

              <div className="mb-5 grid grid-cols-2 rounded-md bg-slate-100 p-1 text-sm">
                <Link
                  to={`/login${location.search}`}
                  className={`rounded px-3 py-2 text-center font-medium ${
                    authMode === "login" ? "bg-white text-slate-950 shadow-sm" : "text-slate-500"
                  }`}
                >
                  Login
                </Link>
                <Link
                  to={`/register${location.search}`}
                  className={`rounded px-3 py-2 text-center font-medium ${
                    authMode === "register" ? "bg-white text-slate-950 shadow-sm" : "text-slate-500"
                  }`}
                >
                  Register
                </Link>
              </div>

              <AuthForm
                key={authMode}
                mode={authMode}
                isPending={mutation.isPending}
                errorMessage={mutation.error?.message}
                onSubmit={(values) => mutation.mutate(values)}
              />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function defaultRouteForRole(role: string): string {
  if (role === "driver") {
    return "/driver";
  }
  if (role === "admin") {
    return "/admin";
  }
  return "/app";
}
