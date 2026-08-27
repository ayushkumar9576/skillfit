import AuthGuard from "@/components/guards/AuthGuard";

export default function CompleteProfileLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4 sm:p-6 lg:p-8">
        {children}
      </div>
    </AuthGuard>
  );
}
