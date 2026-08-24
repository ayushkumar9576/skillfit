"use client";

/**
 * components/dashboard/ProfileCard.tsx
 * ----------------------------------------
 * Displays the authenticated user's profile information.
 * Only renders fields that the backend actually returns (UserResponseSchema).
 * No fabricated data (no "Member Since", no "Last Login").
 *
 * Error state: Shows an error alert with a refresh option if /auth/me fails.
 */

import { motion } from "framer-motion";
import { RefreshCw, User, Mail, Hash, Shield, BadgeCheck, BadgeX } from "lucide-react";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { SkeletonCard } from "@/components/shared/LoadingSkeleton";
import ErrorAlert from "@/components/shared/ErrorAlert";

export default function ProfileCard() {
  const { data: user, isLoading, isError, error, refetch } = useCurrentUser();

  if (isLoading) return <SkeletonCard />;

  if (isError) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Profile</h3>
        <ErrorAlert
          message={error?.message ?? "Unable to load profile information. Please refresh the page."}
          className="mb-3"
        />
        <button
          type="button"
          onClick={() => refetch()}
          className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Retry
        </button>
      </div>
    );
  }

  const fields = [
    { icon: User, label: "Full Name", value: user?.full_name },
    { icon: Mail, label: "Email", value: user?.email },
    { icon: Hash, label: "Registration No.", value: user?.registration_number },
    { icon: Shield, label: "Role", value: user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : undefined },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.05 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Profile</h3>
        {/* Account status badge — derived from is_active field */}
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
            user?.is_active
              ? "bg-emerald-50 text-emerald-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {user?.is_active
            ? <><BadgeCheck className="h-3.5 w-3.5" aria-hidden="true" /> Active</>
            : <><BadgeX className="h-3.5 w-3.5" aria-hidden="true" /> Inactive</>
          }
        </span>
      </div>

      <dl className="space-y-4">
        {fields.map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-start gap-3">
            <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
            <div className="min-w-0">
              <dt className="text-xs font-medium text-slate-400">{label}</dt>
              <dd className="mt-0.5 truncate text-sm text-slate-900">{value ?? "—"}</dd>
            </div>
          </div>
        ))}
      </dl>
    </motion.div>
  );
}
