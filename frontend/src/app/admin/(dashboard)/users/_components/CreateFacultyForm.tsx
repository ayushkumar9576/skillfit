import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { createFaculty } from "@/lib/api/admin";

const facultySchema = z.object({
  full_name: z.string().min(1, "Full name is required").max(150),
  email: z.string().email("Invalid email address"),
  password: z.string().min(12, "Password must be at least 12 characters"),
  registration_number: z.string().regex(/^\d{8}$/, "Must be exactly 8 digits"),
  department: z.string().optional(),
});

type FacultyFormData = z.infer<typeof facultySchema>;

export default function CreateFacultyForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FacultyFormData>({
    resolver: zodResolver(facultySchema),
  });

  const onSubmit = async (data: FacultyFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);
      setSuccess(false);
      await createFaculty(data);
      setSuccess(true);
      reset();
    } catch (err) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const errorResponse = err as any;
      setError(errorResponse.response?.data?.detail || "Failed to create faculty.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm font-medium">
          {error}
        </div>
      )}
      
      {success && (
        <div className="p-4 bg-emerald-50 text-emerald-700 rounded-lg text-sm font-medium">
          Faculty account created successfully.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Full Name *</label>
          <input
            {...register("full_name")}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
            placeholder="Dr. John Smith"
          />
          {errors.full_name && <p className="text-xs text-red-500">{errors.full_name.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Email Address *</label>
          <input
            {...register("email")}
            type="email"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
            placeholder="john.smith@university.edu"
          />
          {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Registration Number *</label>
          <input
            {...register("registration_number")}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
            placeholder="98765432"
          />
          {errors.registration_number && <p className="text-xs text-red-500">{errors.registration_number.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Temporary Password *</label>
          <input
            {...register("password")}
            type="password"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
            placeholder="Minimum 12 characters"
          />
          {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-700">Department (Optional)</label>
        <input
          {...register("department")}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-slate-900"
          placeholder="Computer Science & Engineering"
        />
        {errors.department && <p className="text-xs text-red-500">{errors.department.message}</p>}
      </div>

      <div className="pt-4 flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
        >
          {isSubmitting ? "Creating..." : "Create Faculty Account"}
        </button>
      </div>
    </form>
  );
}
