/**
 * Navigation configuration for SkillFit dashboard layouts.
 *
 * Icons are stored as plain string names — NOT as component references —
 * because these arrays are passed from Server Components (layout.tsx files)
 * into Client Components (DashboardShell). React cannot serialize component
 * references (functions / objects with $$typeof) across that boundary.
 *
 * The actual Lucide components are resolved inside Client Components via
 * the `iconMap` exported from this file.
 */
import {
  UploadCloud,
  LayoutDashboard,
  FileBarChart,
  Target,
  User,
  Settings,
  Users,
  FileText,
  type LucideIcon,
} from "lucide-react";

export const iconMap: Record<string, LucideIcon> = {
  UploadCloud,
  LayoutDashboard,
  FileBarChart,
  Target,
  User,
  Settings,
  Users,
  FileText,
};

export interface NavItem {
  label: string;
  href: string;
  /** Plain icon name key — resolved to a component via `iconMap` in Client Components. */
  icon?: string;
}

export const studentNavigation: NavItem[] = [
  { label: "Upload CV",       href: "/student/resume",    icon: "UploadCloud" },
  { label: "Dashboard",       href: "/student/dashboard", icon: "LayoutDashboard" },
  { label: "CV Analysis",     href: "/student/analysis",  icon: "FileBarChart" },
  { label: "Placement Match", href: "/student/placement", icon: "Target" },
  { label: "Profile",         href: "/student/profile",   icon: "User" },
  { label: "Settings",        href: "/student/settings",  icon: "Settings" },
];

export const facultyNavigation: NavItem[] = [
  { label: "Dashboard", href: "/faculty/dashboard", icon: "LayoutDashboard" },
  { label: "Profile",   href: "/faculty/profile",   icon: "User" },
];

export const adminNavigation: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard", icon: "LayoutDashboard" },
  { label: "Users",     href: "/admin/users",     icon: "Users" },
  { label: "Resumes",   href: "/admin/resumes",   icon: "FileText" },
  { label: "Profile",   href: "/admin/profile",   icon: "User" },
];
