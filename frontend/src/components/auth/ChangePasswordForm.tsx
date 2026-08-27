"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { changePassword } from "@/lib/api/auth";
import { useAuthContext } from "@/providers/AuthProvider";
import { parseApiError } from "@/lib/utils";
import ErrorAlert from "@/components/shared/ErrorAlert";
import { useRouter } from "next/navigation";

const changePasswordSchema = z.object({
  current_password: z.string().min(1, "Current password is required"),
  new_password: z.string().min(12, "New password must be at least 12 characters"),
  confirm_password: z.string().min(1, "Please confirm your new password"),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export default function ChangePasswordForm() {
  const { user, refreshUser } = useAuthContext();
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  });

  const onSubmit = async (data: ChangePasswordFormData) => {
    setApiError(null);
    try {
      await changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      });
      // Update local state to trigger guard redirect
      await refreshUser();
      if (user?.role) {
        router.replace(`/${user.role}/dashboard`);
      } else {
        router.replace("/");
      }
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
        {/* Current Password */}
        <div>
          <label htmlFor="current_password" className="mb-1.5 block text-sm font-medium text-slate-700">
            Current Password
          </label>
          <input
            id="current_password"
            type="password"
            {...register("current_password")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.current_password && (
            <p className="mt-1 text-xs text-red-600">{errors.current_password.message}</p>
          )}
        </div>

        {/* New Password */}
        <div>
          <label htmlFor="new_password" className="mb-1.5 block text-sm font-medium text-slate-700">
            New Password
          </label>
          <input
            id="new_password"
            type="password"
            {...register("new_password")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.new_password && (
            <p className="mt-1 text-xs text-red-600">{errors.new_password.message}</p>
          )}
        </div>

        {/* Confirm Password */}
        <div>
          <label htmlFor="confirm_password" className="mb-1.5 block text-sm font-medium text-slate-700">
            Confirm New Password
          </label>
          <input
            id="confirm_password"
            type="password"
            {...register("confirm_password")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
          {errors.confirm_password && (
            <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60 transition-all duration-200"
        >
          {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {isSubmitting ? "Updating..." : "Update Password"}
        </button>
      </form>
    </div>
  );
}
