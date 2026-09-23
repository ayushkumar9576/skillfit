import AuthGuard from "@/components/guards/AuthGuard";
import RoleGuard from "@/components/guards/RoleGuard";
import DashboardShell from "@/components/layout/DashboardShell";
import { adminNavigation } from "@/config/navigation";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <RoleGuard allowedRole="admin">
        {/* Admins do not require onboarding guard */}
        <DashboardShell navigation={adminNavigation}>
          {children}
        </DashboardShell>
      </RoleGuard>
    </AuthGuard>
  );
}
