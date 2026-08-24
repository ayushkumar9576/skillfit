"use client";

/**
 * components/auth/LoginForm.tsx
 * --------------------------------
 * Login form using registration_number + password.
 * Email is NOT used for authentication — per backend LoginSchema.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { loginUser } from "@/lib/api/auth";
import { useAuth } from "@/hooks/useAuth";
import { parseApiError } from "@/lib/utils";
import ErrorAlert from "@/components/shared/ErrorAlert";

const loginSchema = z.object({
  registration_number: z
    .string()
    .min(1, "Registration number is required")
    .trim(),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setApiError(null);
    try {
      const tokenResponse = await loginUser({
        registration_number: data.registration_number,
        password: data.password,
      });
      await login(tokenResponse.access_token);
      router.push("/dashboard");
    } catch (err) {
      const parsed = parseApiError(err);
      setApiError(parsed.message);
    }
  };

  return (
    <div className="w-full max-w-md">
      {apiError && (
        <ErrorAlert
          message={apiError}
          onDismiss={() => setApiError(null)}
          className="mb-5"
        />
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Registration Number */}
        <div>
          <label htmlFor="login-reg-number" className="mb-1.5 block text-sm font-medium text-slate-700">
            Registration Number
          </label>
          <input
            id="login-reg-number"
            type="text"
            autoComplete="username"
            placeholder="2021CSE001"
            {...register("registration_number")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.registration_number && (
            <p className="mt-1 text-xs text-red-600">{errors.registration_number.message}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <label htmlFor="login-password" className="mb-1.5 block text-sm font-medium text-slate-700">
            Password
          </label>
          <div className="relative">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="Your password"
              {...register("password")}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 pr-10 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60 transition-all duration-200"
          aria-busy={isSubmitting}
        >
          {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
          {isSubmitting ? "Signing in…" : "Sign In"}
        </button>
      </form>
    </div>
  );
}
