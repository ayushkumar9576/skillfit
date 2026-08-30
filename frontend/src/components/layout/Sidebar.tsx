"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap } from "lucide-react";
import { iconMap } from "@/config/navigation";
import type { NavItem } from "@/config/navigation";

interface SidebarProps {
  navigation: NavItem[];
  onItemClick?: () => void;
}

export default function Sidebar({ navigation, onItemClick }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className="flex grow flex-col overflow-y-auto border-r border-slate-200 bg-white px-6 pb-4">
      <div className="flex h-16 shrink-0 items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600">
          <Zap className="h-4 w-4 text-white" aria-hidden="true" />
        </div>
        <span className="text-xl font-bold tracking-tight text-slate-900">SkillFit</span>
      </div>
      <nav className="mt-8 flex flex-1 flex-col">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="-mx-2 space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                // Resolve the icon component from the string name — safe in a Client Component
                const Icon = item.icon ? iconMap[item.icon] : undefined;
                return (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      onClick={onItemClick}
                      className={`
                        group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold
                        ${isActive ? "bg-indigo-50 text-indigo-600" : "text-slate-700 hover:bg-slate-50 hover:text-indigo-600"}
                      `}
                    >
                      {Icon && (
                        <Icon
                          className={`h-6 w-6 shrink-0 ${isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-indigo-600"}`}
                          aria-hidden="true"
                        />
                      )}
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </li>
        </ul>
      </nav>
    </div>
  );
}
