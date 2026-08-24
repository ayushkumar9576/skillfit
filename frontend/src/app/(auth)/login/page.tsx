"use client";

/**
 * app/(auth)/login/page.tsx
 * -------------------------
 * Login page route (/login).
 * Redirects already-authenticated users to /dashboard.
 * useSearchParams is wrapped in Suspense per Next.js requirement.
 */

import Link from "next/link";
import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Zap } from "lucide-react";
import LoginForm from "@/components/auth/LoginForm";
import { useAuth } from "@/hooks/useAuth";

/** Inner component that reads searchParams — must be inside Suspense. */
function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();
  const justRegistered = searchParams.get("registered") === "true";

  // Redirect authenticated users away from the login page
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) return null;

  return (
    <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-md">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center text-center">
        <Link
          href="/"
          className="mb-4 flex items-center gap-2 font-semibold text-slate-900 hover:opacity-80 transition-opacity"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600">
            <Zap className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <span className="text-xl tracking-tight">SkillFit</span>
        </Link>
        <h1 className="text-xl font-bold text-slate-900">Welcome back</h1>
        <p className="mt-1 text-sm text-slate-500">Sign in to your SkillFit account</p>
      </div>

      {/* Post-registration success message */}
      {justRegistered && (
        <div className="mb-5 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          Account created successfully. You can now sign in.
        </div>
      )}

      <LoginForm />

      {/* Register link */}
      <p className="mt-6 text-center text-sm text-slate-500">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}

/** Page wrapper — Suspense required for useSearchParams in Next.js static builds. */
export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12">
      <Suspense
        fallback={
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-md">
            <div className="flex flex-col items-center gap-3">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" aria-hidden="true" />
              <p className="text-sm text-slate-500">Loading…</p>
            </div>
          </div>
        }
      >
        <LoginPageContent />
      </Suspense>
    </div>
  );
}
