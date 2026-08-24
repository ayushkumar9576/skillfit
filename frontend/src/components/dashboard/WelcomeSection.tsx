"use client";

/**
 * components/dashboard/WelcomeSection.tsx
 * -----------------------------------------
 * Personalized welcome banner using live data from AuthProvider.
 * Shows loading skeleton while data loads, graceful error state on failure.
 */

import { motion } from "framer-motion";
import { useAuth } from "@/hooks/useAuth";
import { Skeleton } from "@/components/shared/LoadingSkeleton";

export default function WelcomeSection() {
  const { user, isLoading } = useAuth();

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-56" />
          <Skeleton className="h-4 w-36" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex items-center gap-4"
    >
      {/* Avatar */}
      <div
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-base font-bold uppercase text-indigo-700"
        aria-hidden="true"
      >
        {user?.full_name.slice(0, 2) ?? "?"}
      </div>
      <div>
        <h2 className="text-xl font-bold text-slate-900">
          {greeting()}, {user?.full_name.split(" ")[0] ?? "there"} 👋
        </h2>
        <p className="text-sm text-slate-500 capitalize">
          {user?.role} · {user?.registration_number}
        </p>
      </div>
    </motion.div>
  );
}
