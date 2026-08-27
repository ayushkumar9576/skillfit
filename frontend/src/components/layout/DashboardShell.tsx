"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import MobileNav from "./MobileNav";
import type { NavItem } from "@/config/navigation";

interface DashboardShellProps {
  children: React.ReactNode;
  navigation: NavItem[];
}

export default function DashboardShell({ children, navigation }: DashboardShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Desktop Sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <Sidebar navigation={navigation} />
      </div>

      {/* Mobile Navigation */}
      <MobileNav 
        navigation={navigation} 
        open={mobileMenuOpen} 
        setOpen={setMobileMenuOpen} 
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col lg:pl-64">
        <Header onOpenMobileMenu={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
