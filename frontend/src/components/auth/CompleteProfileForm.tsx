"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { updateProfile } from "@/lib/api/profile";
import { useAuthContext } from "@/providers/AuthProvider";
import { parseApiError } from "@/lib/utils";
import ErrorAlert from "@/components/shared/ErrorAlert";
import { useRouter } from "next/navigation";

// Base schema for both roles
const baseProfileSchema = z.object({
  phone: z.string().optional(),
  linkedin_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  github_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  portfolio_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
});

// Student specific schema
const studentSchema = baseProfileSchema.extend({
  branch: z.string().min(1, "Branch is required"),
  cgpa: z.coerce.number().min(0).max(10).optional(),
});

// Faculty specific schema
const facultySchema = baseProfileSchema.extend({
  department: z.string().min(1, "Department is required"),
});

export default function CompleteProfileForm() {
  const { user, refreshUser } = useAuthContext();
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);

  const isStudent = user?.role === "student";
  const schema = isStudent ? studentSchema : facultySchema;
  
  type ProfileFormData = z.infer<typeof studentSchema> & z.infer<typeof facultySchema>;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(schema) as any,
  });

  const onSubmit = async (data: ProfileFormData) => {
    setApiError(null);
    try {
      // Remove empty strings for optional URL fields before sending
      const payload = { ...data };
      if (payload.linkedin_url === "") delete payload.linkedin_url;
      if (payload.github_url === "") delete payload.github_url;
      if (payload.portfolio_url === "") delete payload.portfolio_url;
      
      await updateProfile(payload);
      
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
    <div className="w-full">
      {apiError && (
        <ErrorAlert
          message={apiError}
          onDismiss={() => setApiError(null)}
          className="mb-5"
        />
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">
        
        {/* Dynamic Role Fields */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {isStudent ? (
            <>
              <div>
                <label htmlFor="branch" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Branch <span className="text-red-500">*</span>
                </label>
                <input
                  id="branch"
                  type="text"
                  placeholder="e.g. Computer Science"
                  {...register("branch")}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
                />

                {errors.branch && <p className="mt-1 text-xs text-red-600">{errors.branch.message}</p>}
              </div>
              <div>
                <label htmlFor="cgpa" className="mb-1.5 block text-sm font-medium text-slate-700">
                  CGPA
                </label>
                <input
                  id="cgpa"
                  type="number"
                  step="0.01"
                  placeholder="e.g. 8.5"
                  {...register("cgpa")}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
                />

                {errors.cgpa && <p className="mt-1 text-xs text-red-600">{errors.cgpa.message}</p>}
              </div>
            </>
          ) : (
            <div className="sm:col-span-2">
              <label htmlFor="department" className="mb-1.5 block text-sm font-medium text-slate-700">
                Department <span className="text-red-500">*</span>
              </label>
              <input
                id="department"
                type="text"
                placeholder="e.g. Computer Science"
                {...register("department")}
                className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
              />

              {errors.department && <p className="mt-1 text-xs text-red-600">{errors.department.message}</p>}
            </div>
          )}
        </div>

        {/* Common Fields */}
        <div>
          <label htmlFor="phone" className="mb-1.5 block text-sm font-medium text-slate-700">
            Phone Number
          </label>
          <input
            id="phone"
            type="tel"
            placeholder="+1 234 567 8900"
            {...register("phone")}
            className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
          />
        </div>

        {/* Professional URLs */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-slate-900">Professional Links (Optional)</h3>
          
          <div>
            <label htmlFor="linkedin_url" className="sr-only">LinkedIn URL</label>
            <input
              id="linkedin_url"
              type="url"
              placeholder="https://linkedin.com/in/username"
              {...register("linkedin_url")}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
            />

            {errors.linkedin_url && <p className="mt-1 text-xs text-red-600">{errors.linkedin_url.message}</p>}
          </div>

          <div>
            <label htmlFor="github_url" className="sr-only">GitHub URL</label>
            <input
              id="github_url"
              type="url"
              placeholder="https://github.com/username"
              {...register("github_url")}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
            />

            {errors.github_url && <p className="mt-1 text-xs text-red-600">{errors.github_url.message}</p>}
          </div>

          <div>
            <label htmlFor="portfolio_url" className="sr-only">Portfolio URL</label>
            <input
              id="portfolio_url"
              type="url"
              placeholder="https://yourportfolio.com"
              {...register("portfolio_url")}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
            />

            {errors.portfolio_url && <p className="mt-1 text-xs text-red-600">{errors.portfolio_url.message}</p>}
          </div>
        </div>

        {/* Submit */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60 transition-all duration-200"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "Saving..." : "Complete Profile"}
          </button>
        </div>
      </form>
    </div>
  );
}
