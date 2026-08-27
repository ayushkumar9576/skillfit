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
import Card from "@/components/shared/Card";

const profileSchema = z.object({
  branch: z.string().min(1, "Branch is required"),
  cgpa: z.coerce.number().min(0).max(10).optional(),
  phone: z.string().optional(),
  linkedin_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  github_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  portfolio_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function ProfileEditor() {
  const { user, refreshUser } = useAuthContext();
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(profileSchema) as any,
    defaultValues: {
      branch: user?.branch || "",
      cgpa: user?.cgpa || undefined,
      phone: user?.phone || "",
      linkedin_url: user?.linkedin_url || "",
      github_url: user?.github_url || "",
      portfolio_url: user?.portfolio_url || "",
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    setApiError(null);
    setSuccessMessage(null);
    try {
      const payload = { ...data };
      if (payload.linkedin_url === "") delete payload.linkedin_url;
      if (payload.github_url === "") delete payload.github_url;
      if (payload.portfolio_url === "") delete payload.portfolio_url;
      
      await updateProfile(payload);
      await refreshUser();
      setSuccessMessage("Profile updated successfully.");
    } catch (err) {
      const parsed = parseApiError(err);
      setApiError(parsed.message);
    }
  };

  return (
    <Card className="max-w-3xl">
      <div className="px-6 py-5 border-b border-slate-200">
        <h2 className="text-lg font-bold text-slate-800">Personal Information</h2>
        <p className="text-sm text-slate-500">Update your academic and contact details.</p>
      </div>

      <div className="p-6">
        {apiError && (
          <ErrorAlert
            message={apiError}
            onDismiss={() => setApiError(null)}
            className="mb-6"
          />
        )}

        {successMessage && (
          <div className="mb-6 rounded-lg bg-emerald-50 p-4 border border-emerald-200 flex items-center justify-between">
            <p className="text-sm font-medium text-emerald-800">{successMessage}</p>
            <button onClick={() => setSuccessMessage(null)} className="text-emerald-600 hover:text-emerald-800">
              &times;
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.full_name || ""}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-500 cursor-not-allowed"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Registration Number</label>
              <input
                type="text"
                disabled
                value={user?.registration_number || ""}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-500 cursor-not-allowed"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="branch" className="mb-1.5 block text-sm font-medium text-slate-700">
                Branch <span className="text-red-500">*</span>
              </label>
              <input
                id="branch"
                type="text"
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
                {...register("cgpa")}
                className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
              />
              {errors.cgpa && <p className="mt-1 text-xs text-red-600">{errors.cgpa.message}</p>}
            </div>
          </div>

          <div>
            <label htmlFor="phone" className="mb-1.5 block text-sm font-medium text-slate-700">
              Phone Number
            </label>
            <input
              id="phone"
              type="tel"
              {...register("phone")}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
            />
          </div>

          <div className="space-y-4 pt-4 border-t border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900">Professional Links</h3>
            
            <div>
              <label htmlFor="linkedin_url" className="sr-only">LinkedIn URL</label>
              <input
                id="linkedin_url"
                type="url"
                placeholder="LinkedIn Profile URL"
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
                placeholder="GitHub Profile URL"
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
                placeholder="Personal Portfolio URL"
                {...register("portfolio_url")}
                className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition-colors"
              />
              {errors.portfolio_url && <p className="mt-1 text-xs text-red-600">{errors.portfolio_url.message}</p>}
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60 transition-all"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSubmitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </Card>
  );
}
