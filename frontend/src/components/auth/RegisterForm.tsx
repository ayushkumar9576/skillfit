"use client";

/**
 * components/auth/RegisterForm.tsx
 * ----------------------------------
 * Student/Faculty registration form with:
 *  - Role toggle (Student / Faculty)
 *  - React Hook Form + Zod validation
 *  - Live password strength meter
 *  - API integration with exact backend DTOs
 *  - Comprehensive error handling
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { registerStudent, registerFaculty } from "@/lib/api/auth";
import { parseApiError } from "@/lib/utils";
import ErrorAlert from "@/components/shared/ErrorAlert";
import PasswordStrengthMeter from "@/components/auth/PasswordStrengthMeter";

// Zod schema — mirrors RegisterStudentSchema & RegisterFacultySchema password rules
const registerSchema = z
  .object({
    full_name: z
      .string()
      .min(1, "Full name is required")
      .max(150, "Full name must be under 150 characters")
      .trim(),
    email: z.string().email("Please enter a valid email address"),
    registration_number: z
      .string()
      .min(1, "Registration number is required")
      .max(50, "Registration number must be under 50 characters")
      .trim(),
    password: z
      .string()
      .min(12, "Password must be at least 12 characters"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;
type UserRole = "student" | "faculty";

export default function RegisterForm() {
  const router = useRouter();
  const [role, setRole] = useState<UserRole>("student");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const passwordValue = watch("password", "");

  const onSubmit = async (data: RegisterFormData) => {
    setApiError(null);
    try {
      const payload = {
        full_name: data.full_name,
        email: data.email,
        registration_number: data.registration_number,
        password: data.password,
      };
      if (role === "student") {
        await registerStudent(payload);
      } else {
        await registerFaculty(payload);
      }
      router.push("/login?registered=true");
    } catch (err) {
      const parsed = parseApiError(err);
      setApiError(parsed.message);
    }
  };

  return (
    <div className="w-full max-w-md">
      {/* Role toggle */}
      <div className="mb-6 flex rounded-xl border border-slate-200 bg-slate-50 p-1">
        {(["student", "faculty"] as UserRole[]).map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRole(r)}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all duration-200 ${
              role === r
                ? "bg-white text-indigo-700 shadow-sm border border-slate-200"
                : "text-slate-500 hover:text-slate-700"
            }`}
            aria-pressed={role === r}
          >
            {r.charAt(0).toUpperCase() + r.slice(1)}
          </button>
        ))}
      </div>

      {/* API Error */}
      {apiError && (
        <ErrorAlert
          message={apiError}
          onDismiss={() => setApiError(null)}
          className="mb-5"
        />
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Full Name */}
        <div>
          <label htmlFor="reg-full-name" className="mb-1.5 block text-sm font-medium text-slate-700">
            Full Name
          </label>
          <input
            id="reg-full-name"
            type="text"
            autoComplete="name"
            placeholder="Aarav Sharma"
            {...register("full_name")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.full_name && (
            <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="reg-email" className="mb-1.5 block text-sm font-medium text-slate-700">
            Email Address
          </label>
          <input
            id="reg-email"
            type="email"
            autoComplete="email"
            placeholder="aarav@university.edu"
            {...register("email")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.email && (
            <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
          )}
        </div>

        {/* Registration Number */}
        <div>
          <label htmlFor="reg-reg-number" className="mb-1.5 block text-sm font-medium text-slate-700">
            Registration Number
          </label>
          <input
            id="reg-reg-number"
            type="text"
            autoComplete="username"
            placeholder="2021CSE001"
            {...register("registration_number")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.registration_number && (
            <p className="mt-1 text-xs text-red-600">{errors.registration_number.message}</p>
          )}
          <p className="mt-1 text-xs text-slate-400">Your university-issued registration number</p>
        </div>

        {/* Password */}
        <div>
          <label htmlFor="reg-password" className="mb-1.5 block text-sm font-medium text-slate-700">
            Password
          </label>
          <div className="relative">
            <input
              id="reg-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder="Minimum 12 characters"
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
          <PasswordStrengthMeter password={passwordValue} />
        </div>

        {/* Confirm Password */}
        <div>
          <label htmlFor="reg-confirm-password" className="mb-1.5 block text-sm font-medium text-slate-700">
            Confirm Password
          </label>
          <div className="relative">
            <input
              id="reg-confirm-password"
              type={showConfirm ? "text" : "password"}
              autoComplete="new-password"
              placeholder="Re-enter your password"
              {...register("confirm_password")}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 pr-10 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
            >
              {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>
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
          {isSubmitting ? "Creating account…" : `Create ${role.charAt(0).toUpperCase() + role.slice(1)} Account`}
        </button>
      </form>
    </div>
  );
}
