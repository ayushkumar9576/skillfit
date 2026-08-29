import { 
  LucideIcon, 
  UploadCloud, 
  LayoutDashboard, 
  FileBarChart, 
  Target, 
  User, 
  Settings, 
  Users, 
  FileText 
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon?: LucideIcon;
}

export const studentNavigation: NavItem[] = [
  { label: "Upload CV", href: "/student/resume", icon: UploadCloud },
  { label: "Dashboard", href: "/student/dashboard", icon: LayoutDashboard },
  { label: "CV Analysis", href: "/student/analysis", icon: FileBarChart },
  { label: "Placement Match", href: "/student/placement", icon: Target },
  { label: "Profile", href: "/student/profile", icon: User },
  { label: "Settings", href: "/student/settings", icon: Settings },
];

export const facultyNavigation: NavItem[] = [
  { label: "Dashboard", href: "/faculty/dashboard", icon: LayoutDashboard },
  { label: "Profile", href: "/faculty/profile", icon: User },
];

export const adminNavigation: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { label: "Users", href: "/admin/users", icon: Users },
  { label: "Resumes", href: "/admin/resumes", icon: FileText },
  { label: "Profile", href: "/admin/profile", icon: User },
];
