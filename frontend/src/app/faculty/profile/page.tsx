"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuthContext } from "@/providers/AuthProvider";
import { updateProfile } from "@/lib/api/profile";
import PageHeader from "@/components/shared/PageHeader";

const profileSchema = z.object({
  department: z.string().min(1, "Department is required").max(150),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function FacultyProfilePage() {
  const { user, refreshUser } = useAuthContext();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      department: "", // Default to empty string since department isn't in User schema yet until refetch, though faculty dashboard exposes it.
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);
      setSuccess(false);
      await updateProfile(data);
      await refreshUser();
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update profile.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader 
        title="Faculty Profile" 
        description="Manage your academic department and account details."
      />

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-6 md:p-8 space-y-8">
          
          <div>
            <h3 className="text-lg font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">Account Information (Read-Only)</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="text-sm font-medium text-slate-500">Full Name</label>
                <p className="mt-1 font-medium text-slate-900">{user.full_name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-500">Email Address</label>
                <p className="mt-1 font-medium text-slate-900">{user.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-500">Registration Number</label>
                <p className="mt-1 font-medium text-slate-900">{user.registration_number}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">Academic Profile</h3>
            
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {error && (
                <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm font-medium">
                  {error}
                </div>
              )}
              
              {success && (
                <div className="p-4 bg-emerald-50 text-emerald-700 rounded-lg text-sm font-medium">
                  Profile updated successfully.
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Department *</label>
                <input
                  {...register("department")}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
                  placeholder="e.g. Computer Science & Engineering"
                />
                {errors.department && <p className="text-xs text-red-500">{errors.department.message}</p>}
                <p className="text-xs text-slate-500">This will be displayed to your mentored students.</p>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}
