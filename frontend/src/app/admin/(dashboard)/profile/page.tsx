"use client";

import Link from "next/link";
import { useAuthContext } from "@/providers/AuthProvider";
import PageHeader from "@/components/shared/PageHeader";
import { UserCircle, Shield, CheckCircle2, XCircle, Settings, Mail, BadgeInfo } from "lucide-react";

export default function AdminProfilePage() {
  const { user } = useAuthContext();

  if (!user) return null;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <PageHeader
        title="Admin Profile"
        description="Manage your administrator account settings and system identity."
      />

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {/* Left Column: Account Summary */}
        <div className="md:col-span-1 space-y-6">
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col items-center border-b border-slate-100 p-8 text-center">
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-indigo-50 text-indigo-600 ring-4 ring-white shadow-sm">
                <UserCircle className="h-10 w-10" />
              </div>
              <h2 className="text-lg font-semibold text-slate-900">{user.full_name}</h2>
              <p className="text-sm font-medium text-slate-500 capitalize">{user.role}</p>
            </div>
            <div className="bg-slate-50 px-6 py-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Status</span>
                {user.is_active ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
                    <XCircle className="h-3.5 w-3.5" />
                    Inactive
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Detailed Information & Security */}
        <div className="md:col-span-2 space-y-8">
          {/* Identity Information Section */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="border-b border-slate-100 px-6 py-5">
              <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <BadgeInfo className="h-5 w-5 text-indigo-500" />
                Identity Information
              </h3>
            </div>
            <div className="px-6 py-5">
              <dl className="space-y-6">
                <div>
                  <dt className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                    <Mail className="h-4 w-4" /> Email Address
                  </dt>
                  <dd className="text-sm text-slate-900">{user.email}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1">
                    <Shield className="h-4 w-4" /> Registration Number
                  </dt>
                  <dd className="text-sm text-slate-900">{user.registration_number}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500 mb-1">Profile Onboarding</dt>
                  <dd className="text-sm text-slate-900 flex items-center gap-2">
                    {user.profile_completed ? "Completed (Bypassed for Admins)" : "Pending"}
                  </dd>
                </div>
              </dl>
            </div>
          </section>

          {/* Security Section */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="border-b border-slate-100 px-6 py-5">
              <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <Settings className="h-5 w-5 text-indigo-500" />
                Security Settings
              </h3>
            </div>
            <div className="px-6 py-5">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-900">Account Password</h4>
                  <p className="text-sm text-slate-500 mt-1">
                    Ensure your account is using a long, random password to stay secure.
                  </p>
                </div>
                <Link
                  href="/change-password"
                  className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 shadow-sm hover:bg-slate-50 hover:text-indigo-600 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Change Password
                </Link>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
