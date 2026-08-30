"use client";

import TopNavigation from "./TopNavigation";
import type { NavItem } from "@/config/navigation";

interface DashboardShellProps {
  children: React.ReactNode;
  navigation: NavItem[];
}

export default function DashboardShell({ children, navigation }: DashboardShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      {/* Top Navigation Bar */}
      <TopNavigation navigation={navigation} />

      {/* Main Content Area */}
      <main className="flex-1 w-full p-4 sm:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
