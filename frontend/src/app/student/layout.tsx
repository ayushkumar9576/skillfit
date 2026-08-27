import AuthGuard from "@/components/guards/AuthGuard";
import RoleGuard from "@/components/guards/RoleGuard";
import OnboardingGuard from "@/components/guards/OnboardingGuard";
import DashboardShell from "@/components/layout/DashboardShell";
import { studentNavigation } from "@/config/navigation";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <RoleGuard allowedRole="student">
        <OnboardingGuard>
          <DashboardShell navigation={studentNavigation}>
            {children}
          </DashboardShell>
        </OnboardingGuard>
      </RoleGuard>
    </AuthGuard>
  );
}
