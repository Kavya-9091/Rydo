import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, Loader2, Lock, Mail, Phone, UserRound } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import type { FieldErrors } from "react-hook-form";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { UserRole } from "../../types/auth";

const registerSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  phone_number: z.string().regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit mobile number"),
  full_name: z.string().min(2, "Full name is required").max(255),
  role: z.enum(["customer", "driver", "admin"]),
});

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

interface AuthFormProps {
  mode: "login" | "register";
  isPending: boolean;
  errorMessage?: string;
  onSubmit: (values: LoginValues | RegisterValues) => void;
}

export function AuthForm({ mode, isPending, errorMessage, onSubmit }: AuthFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const schema = mode === "register" ? registerSchema : loginSchema;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues | RegisterValues>({
    resolver: zodResolver(schema),
    defaultValues:
      mode === "register"
        ? { email: "", password: "", phone_number: "", full_name: "", role: "customer" as UserRole }
        : { email: "", password: "" },
  });
  const registerErrors = errors as FieldErrors<RegisterValues>;

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
      {mode === "register" && (
        <Field
          icon={<UserRound size={18} />}
          error={registerErrors.full_name?.message}
          input={
            <input
              {...register("full_name")}
              autoComplete="name"
              placeholder="Full name"
              className="w-full bg-transparent outline-none"
            />
          }
        />
      )}

      <Field
        icon={<Mail size={18} />}
        error={errors.email?.message}
        input={
          <input
            {...register("email")}
            autoComplete="email"
            placeholder="Email"
            className="w-full bg-transparent outline-none"
          />
        }
      />

      {mode === "register" && (
        <Field
          icon={<Phone size={18} />}
          error={registerErrors.phone_number?.message}
          input={
            <input
              {...register("phone_number")}
              autoComplete="tel"
              inputMode="numeric"
              maxLength={10}
              placeholder="Phone number"
              className="w-full bg-transparent outline-none"
              onInput={(event) => {
                event.currentTarget.value = event.currentTarget.value.replace(/\D/g, "").slice(0, 10);
              }}
            />
          }
        />
      )}

      <Field
        icon={<Lock size={18} />}
        error={errors.password?.message}
        input={
          <div className="flex w-full items-center gap-2">
            <input
              {...register("password")}
              type={showPassword ? "text" : "password"}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              placeholder="Password"
              className="w-full bg-transparent outline-none"
            />
            <button
              type="button"
              className="text-slate-500 hover:text-slate-900"
              onClick={() => setShowPassword((value) => !value)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              <Eye size={18} />
            </button>
          </div>
        }
      />

      {mode === "register" && (
        <div>
          <select
            {...register("role")}
            className="h-12 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:border-slate-900"
          >
            <option value="customer">Customer</option>
            <option value="driver">Driver</option>
            <option value="admin">Admin</option>
          </select>
          {registerErrors.role?.message && (
            <p className="mt-1 text-xs text-red-600">{registerErrors.role.message}</p>
          )}
        </div>
      )}

      {errorMessage && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {errorMessage}
        </div>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-70"
      >
        {isPending && <Loader2 size={18} className="animate-spin" />}
        {mode === "register" ? "Create account" : "Sign in"}
      </button>
    </form>
  );
}

function Field({
  icon,
  input,
  error,
}: {
  icon: ReactNode;
  input: ReactNode;
  error?: string;
}) {
  return (
    <div>
      <div className="flex h-12 items-center gap-3 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 focus-within:border-slate-900">
        <span className="text-slate-400">{icon}</span>
        {input}
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
