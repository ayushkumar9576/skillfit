import AuthGuard from "@/components/guards/AuthGuard";
import RoleGuard from "@/components/guards/RoleGuard";
import OnboardingGuard from "@/components/guards/OnboardingGuard";
import DashboardShell from "@/components/layout/DashboardShell";
import { facultyNavigation } from "@/config/navigation";

export default function FacultyLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <RoleGuard allowedRole="faculty">
        <OnboardingGuard>
          <DashboardShell navigation={facultyNavigation}>
            {children}
          </DashboardShell>
        </OnboardingGuard>
      </RoleGuard>
    </AuthGuard>
  );
}
