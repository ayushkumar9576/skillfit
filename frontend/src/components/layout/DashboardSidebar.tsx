"use client";

/**
 * components/layout/DashboardSidebar.tsx
 * ----------------------------------------
 * Left sidebar for the protected dashboard shell.
 * Contains logo, nav items, and user info at the bottom.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Zap, LogOut } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Overview" },
];

export default function DashboardSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-100 bg-white">
      {/* Logo */}
      <div className="flex h-16 shrink-0 items-center border-b border-slate-100 px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900 hover:opacity-80 transition-opacity">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600">
            <Zap className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <span className="text-base tracking-tight">SkillFit</span>
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Dashboard navigation">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Platform
        </p>
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <item.icon
                    className={cn("h-4 w-4", isActive ? "text-indigo-600" : "text-slate-400")}
                    aria-hidden="true"
                  />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User info + Logout */}
      <div className="shrink-0 border-t border-slate-100 p-3">
        {user && (
          <div className="mb-2 flex items-center gap-3 rounded-lg px-3 py-2">
            {/* Avatar initials */}
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold uppercase text-indigo-700"
              aria-hidden="true"
            >
              {user.full_name.slice(0, 2)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-slate-900">{user.full_name}</p>
              <p className="truncate text-xs text-slate-400 capitalize">{user.role}</p>
            </div>
          </div>
        )}
        <button
          type="button"
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
