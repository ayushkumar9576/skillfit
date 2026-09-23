import AuthGuard from "@/components/guards/AuthGuard";
import RoleGuard from "@/components/guards/RoleGuard";
import DriveWorkspaceShell from "@/components/drives/DriveWorkspaceShell";

export default function DrivesWorkspaceLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <RoleGuard allowedRole="admin">
        <DriveWorkspaceShell>
          {children}
        </DriveWorkspaceShell>
      </RoleGuard>
    </AuthGuard>
  );
}
