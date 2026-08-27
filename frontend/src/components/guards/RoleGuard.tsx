"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/providers/AuthProvider";
import type { UserRole } from "@/types/auth";

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRole: UserRole;
}

export default function RoleGuard({ children, allowedRole }: RoleGuardProps) {
  const { user, isLoading } = useAuthContext();
  const [isClient, setIsClient] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isLoading && user && user.role !== allowedRole) {
      // Could redirect to their specific dashboard based on role, 
      // but for safety we redirect to root which can handle dispatch.
      router.replace("/");
    }
  }, [isLoading, user, allowedRole, router]);

  // Wait until mounted on client and auth is resolved
  if (!isClient || isLoading || !user) {
    return null;
  }

  if (user.role !== allowedRole) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
        <div className="w-full max-w-md rounded-xl border border-red-200 bg-red-50 p-6 text-center shadow-sm">
          <h2 className="mb-2 text-xl font-bold text-red-800">Access Denied</h2>
          <p className="text-red-600">You do not have permission to view this page.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
