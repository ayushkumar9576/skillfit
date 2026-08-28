"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { updateProfile } from "@/lib/api/profile";
import { useAuthContext } from "@/providers/AuthProvider";
import { parseApiError } from "@/lib/utils";
import ErrorAlert from "@/components/shared/ErrorAlert";

const profileSchema = z.object({
  branch: z.string().min(1, "Branch is required"),
  cgpa: z.coerce.number().min(0, "Invalid CGPA").max(10, "Max 10").optional(),
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
  const [isEditing, setIsEditing] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
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

  const missingFields: string[] = [];
  if (!user?.branch) missingFields.push("Branch");
  if (!user?.cgpa) missingFields.push("CGPA");
  if (!user?.phone) missingFields.push("Phone Number");

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
      setIsEditing(false);
    } catch (err) {
      const parsed = parseApiError(err);
      setApiError(parsed.message);
    }
  };

  return (
    <div className="w-full">
      {/* Status Bar */}
      <div className={`mb-8 p-4 rounded-lg flex items-center justify-between border ${missingFields.length > 0 ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
        <div className="flex items-center gap-3">
          {missingFields.length > 0 ? (
            <AlertCircle className="h-5 w-5 text-amber-600" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          )}
          <div>
            <h3 className={`text-sm font-semibold ${missingFields.length > 0 ? 'text-amber-800' : 'text-emerald-800'}`}>
              {missingFields.length > 0 ? 'Profile Incomplete' : 'Profile Complete'}
            </h3>
            {missingFields.length > 0 && (
              <p className="text-xs text-amber-700 mt-0.5">Missing: {missingFields.join(", ")}</p>
            )}
          </div>
        </div>
      </div>

      {apiError && (
        <ErrorAlert
          message={apiError}
          onDismiss={() => setApiError(null)}
          className="mb-8"
        />
      )}

      {successMessage && (
        <div className="mb-8 rounded-lg bg-emerald-50 p-4 border border-emerald-200 flex items-center justify-between">
          <p className="text-sm font-medium text-emerald-800">{successMessage}</p>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-600 hover:text-emerald-800 font-bold">
            &times;
          </button>
        </div>
      )}

      {!isEditing ? (
        <div className="space-y-10">
          <section>
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Profile Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs font-medium text-slate-500">Full Name</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{user?.full_name || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">Email</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{user?.email || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">Registration Number</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{user?.registration_number || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">Phone Number</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{user?.phone || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">Branch</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{user?.branch || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">CGPA</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{user?.cgpa || "-"}</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Professional Links</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs font-medium text-slate-500">LinkedIn Profile</p>
                <p className="mt-1 text-sm font-medium text-blue-600">
                  {user?.linkedin_url ? <a href={user.linkedin_url} target="_blank" rel="noreferrer" className="hover:underline">{user.linkedin_url}</a> : "-"}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">GitHub Profile</p>
                <p className="mt-1 text-sm font-medium text-blue-600">
                  {user?.github_url ? <a href={user.github_url} target="_blank" rel="noreferrer" className="hover:underline">{user.github_url}</a> : "-"}
                </p>
              </div>
              <div className="md:col-span-2">
                <p className="text-xs font-medium text-slate-500">Personal Portfolio</p>
                <p className="mt-1 text-sm font-medium text-blue-600">
                  {user?.portfolio_url ? <a href={user.portfolio_url} target="_blank" rel="noreferrer" className="hover:underline">{user.portfolio_url}</a> : "-"}
                </p>
              </div>
            </div>
          </section>

          <div className="flex justify-end pt-6">
            <button
              onClick={() => setIsEditing(true)}
              className="rounded-md bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-all"
            >
              Update Profile Details
            </button>
          </div>
        </div>
      ) : (

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-10">
        
        {/* Profile Summary Section */}
        <section>
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Profile Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-500">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.full_name || ""}
                className="w-full rounded-md border-0 bg-slate-50 py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 cursor-not-allowed"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-500">Email</label>
              <input
                type="email"
                disabled
                value={user?.email || ""}
                className="w-full rounded-md border-0 bg-slate-50 py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 cursor-not-allowed"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-500">Registration Number</label>
              <input
                type="text"
                disabled
                value={user?.registration_number || ""}
                className="w-full rounded-md border-0 bg-slate-50 py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 cursor-not-allowed"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="phone" className="text-xs font-medium text-slate-500">Phone Number</label>
              <input
                id="phone"
                type="tel"
                {...register("phone")}
                className="w-full rounded-md border-0 bg-white py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-inset focus:ring-slate-900 transition-shadow"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="branch" className="text-xs font-medium text-slate-500">Branch <span className="text-red-500">*</span></label>
              <input
                id="branch"
                type="text"
                {...register("branch")}
                className={`w-full rounded-md border-0 bg-white py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ${errors.branch ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-slate-900'} transition-shadow`}
              />
              {errors.branch && <p className="text-xs text-red-500 mt-1">{errors.branch.message}</p>}
            </div>
            <div className="space-y-1">
              <label htmlFor="cgpa" className="text-xs font-medium text-slate-500">CGPA</label>
              <input
                id="cgpa"
                type="number"
                step="0.01"
                {...register("cgpa")}
                className={`w-full rounded-md border-0 bg-white py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ${errors.cgpa ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-slate-900'} transition-shadow`}
              />
              {errors.cgpa && <p className="text-xs text-red-500 mt-1">{errors.cgpa.message}</p>}
            </div>
          </div>
        </section>

        {/* Professional Links Section */}
        <section>
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Professional Links</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label htmlFor="linkedin_url" className="text-xs font-medium text-slate-500">LinkedIn Profile</label>
              <input
                id="linkedin_url"
                type="url"
                placeholder="https://linkedin.com/in/..."
                {...register("linkedin_url")}
                className={`w-full rounded-md border-0 bg-white py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ${errors.linkedin_url ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-slate-900'} transition-shadow`}
              />
              {errors.linkedin_url && <p className="text-xs text-red-500 mt-1">{errors.linkedin_url.message}</p>}
            </div>
            <div className="space-y-1">
              <label htmlFor="github_url" className="text-xs font-medium text-slate-500">GitHub Profile</label>
              <input
                id="github_url"
                type="url"
                placeholder="https://github.com/..."
                {...register("github_url")}
                className={`w-full rounded-md border-0 bg-white py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ${errors.github_url ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-slate-900'} transition-shadow`}
              />
              {errors.github_url && <p className="text-xs text-red-500 mt-1">{errors.github_url.message}</p>}
            </div>
            <div className="space-y-1 md:col-span-2">
              <label htmlFor="portfolio_url" className="text-xs font-medium text-slate-500">Personal Portfolio</label>
              <input
                id="portfolio_url"
                type="url"
                placeholder="https://yourwebsite.com"
                {...register("portfolio_url")}
                className={`w-full rounded-md border-0 bg-white py-2.5 px-3 text-sm text-slate-900 ring-1 ring-inset ${errors.portfolio_url ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-slate-900'} transition-shadow`}
              />
              {errors.portfolio_url && <p className="text-xs text-red-500 mt-1">{errors.portfolio_url.message}</p>}
            </div>
          </div>
        </section>

        <div className="flex items-center justify-end gap-4 pt-6">
          <button
            type="button"
            onClick={() => setIsEditing(false)}
            className="rounded-md px-6 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100 transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!isDirty || isSubmitting}
            className="flex items-center justify-center gap-2 rounded-md bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </form>
      )}
    </div>
  );
}
