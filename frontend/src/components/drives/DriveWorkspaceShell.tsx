"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  ArrowLeft, 
  LayoutDashboard, 
  PlusCircle, 
  Clock, 
  CheckCircle2, 
  Globe 
} from "lucide-react";

interface DriveWorkspaceShellProps {
  children: React.ReactNode;
}

const navigation = [
  { name: "Workspace Home", href: "/admin/drives", icon: LayoutDashboard },
  { name: "Create Drive", href: "/admin/drives/create", icon: PlusCircle },
  { name: "Pending Analysis", href: "/admin/drives/pending", icon: Clock },
  { name: "Awaiting Approval", href: "/admin/drives/approvals", icon: CheckCircle2 },
  { name: "Published Drives", href: "/admin/drives/published", icon: Globe },
];

export default function DriveWorkspaceShell({ children }: DriveWorkspaceShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 h-16 flex items-center px-6 justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Link
            href="/admin/dashboard"
            className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors bg-slate-100 hover:bg-slate-200 py-1.5 px-3 rounded-md"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <div className="h-6 w-px bg-slate-200 mx-2" />
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Placement Drive Workspace</h1>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-slate-200 flex-shrink-0 hidden md:flex flex-col">
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? "text-indigo-700" : "text-slate-400"}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
