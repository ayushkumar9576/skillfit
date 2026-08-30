"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, LogOut, User } from "lucide-react";
import type { NavItem } from "@/config/navigation";
import { useAuthContext } from "@/providers/AuthProvider";

interface TopNavigationProps {
  navigation: NavItem[];
}

export default function TopNavigation({ navigation }: TopNavigationProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthContext();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white shadow-sm">
      <div className="mx-auto flex h-16 w-full max-w-full items-center justify-between px-4 sm:px-6 lg:px-8">
        
        {/* Left Section: Logo & Mobile Nav (Scrollable) / Desktop Nav */}
        <div className="flex flex-1 items-center gap-6 overflow-hidden">
          
          {/* Logo */}
          <div className="flex shrink-0 items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600">
              <Zap className="h-4 w-4 text-white" aria-hidden="true" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900 hidden sm:block">
              SkillFit
            </span>
          </div>

          {/* Navigation Links - Horizontally scrollable on mobile, inline on desktop */}
          <nav className="flex-1 overflow-x-auto no-scrollbar mask-edges">
            <ul className="flex items-center gap-2 sm:gap-6 min-w-max px-1 h-16">
              {navigation.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                
                return (
                  <li key={item.label} className="h-full flex items-center">
                    <Link
                      href={item.href}
                      className={`
                        block whitespace-nowrap px-3 py-2 text-sm font-semibold transition-colors rounded-md
                        ${isActive 
                          ? "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200" 
                          : "text-slate-600 hover:bg-slate-50 hover:text-indigo-600"
                        }
                      `}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        {/* Right Section: User Profile & Logout */}
        <div className="flex shrink-0 items-center gap-4 pl-4 ml-auto border-l border-slate-200 h-8">
          <div className="hidden md:flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-600">
              <User className="h-4 w-4" />
            </div>
            <div className="flex flex-col items-start justify-center">
              <span className="text-sm font-semibold leading-none text-slate-900" aria-hidden="true">
                {user?.full_name || "User"}
              </span>
              <span className="text-[10px] text-slate-500 capitalize leading-none mt-1 uppercase tracking-wider font-bold">
                {user?.role}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-2 rounded-md bg-white px-2.5 py-2 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-inset ring-slate-300 hover:bg-slate-50"
            title="Logout"
          >
            <LogOut className="h-4 w-4 text-slate-500" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .mask-edges {
          mask-image: linear-gradient(to right, transparent, black 10px, black calc(100% - 10px), transparent);
        }
      `}} />
    </header>
  );
}