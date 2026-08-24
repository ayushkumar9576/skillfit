"use client";

/**
 * components/shared/LoadingSkeleton.tsx
 * ----------------------------------------
 * Animated pulse skeleton components for loading states.
 * Use these while waiting for API responses to avoid blank screens.
 */

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

/** Base skeleton block with animated pulse. */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-slate-200",
        className
      )}
      aria-hidden="true"
    />
  );
}

/** Skeleton for a text line. */
export function SkeletonText({ className }: SkeletonProps) {
  return <Skeleton className={cn("h-4 w-full", className)} />;
}

/** Skeleton for a heading. */
export function SkeletonHeading({ className }: SkeletonProps) {
  return <Skeleton className={cn("h-7 w-48", className)} />;
}

/** Skeleton for a card block. */
export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div
      className={cn("rounded-xl border border-slate-100 bg-white p-6", className)}
      aria-hidden="true"
    >
      <Skeleton className="mb-4 h-5 w-32" />
      <Skeleton className="mb-2 h-4 w-full" />
      <Skeleton className="mb-2 h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
    </div>
  );
}

/** Full-page skeleton for the dashboard loading state. */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-label="Loading dashboard..." aria-busy="true">
      <div className="flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
      <SkeletonCard className="h-48" />
    </div>
  );
}
