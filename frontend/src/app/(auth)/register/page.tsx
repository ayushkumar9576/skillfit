/**
 * app/(auth)/register/page.tsx
 * ----------------------------
 * Registration page route (/register)
 */

import Link from "next/link";
import { Zap } from "lucide-react";
import RegisterForm from "@/components/auth/RegisterForm";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account — SkillFit",
  description: "Create your SkillFit account to start tracking your placement readiness.",
};

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12">
      {/* Card */}
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center text-center">
          <Link href="/" className="mb-4 flex items-center gap-2 font-semibold text-slate-900 hover:opacity-80 transition-opacity">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600">
              <Zap className="h-4.5 w-4.5 text-white" aria-hidden="true" />
            </div>
            <span className="text-xl tracking-tight">SkillFit</span>
          </Link>
          <h1 className="text-xl font-bold text-slate-900">Create your account</h1>
          <p className="mt-1 text-sm text-slate-500">
            Start your placement intelligence journey
          </p>
        </div>

        <RegisterForm />

        {/* Sign in link */}
        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-700 transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
