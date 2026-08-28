"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthContext } from "@/providers/AuthProvider";

export default function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuthContext();
  const router = useRouter();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isLoading && user) {
      if (user.requires_password_change) {
        if (pathname !== "/change-password") {
          router.replace("/change-password");
        }
      } else if (!user.profile_completed && user.role !== "admin") {
        if (pathname !== "/complete-profile") {
          router.replace("/complete-profile");
        }
      }
    }
  }, [isLoading, user, pathname, router]);

  // Wait until mounted on client and auth is resolved
  if (!isClient || isLoading || !user) {
    return null;
  }

  // If we are about to redirect, don't render children to prevent flashing protected content
  if (user.requires_password_change && pathname !== "/change-password") {
    return null;
  }
  
  if (!user.profile_completed && user.role !== "admin" && pathname !== "/complete-profile") {
    return null;
  }

  return <>{children}</>;
}
