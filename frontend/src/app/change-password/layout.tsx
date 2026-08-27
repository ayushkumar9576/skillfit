import AuthGuard from "@/components/guards/AuthGuard";

export default function ChangePasswordLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
        {children}
      </div>
    </AuthGuard>
  );
}
