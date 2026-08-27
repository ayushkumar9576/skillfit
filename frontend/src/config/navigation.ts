export interface NavItem {
  label: string;
  href: string;
}

export const studentNavigation: NavItem[] = [
  { label: "Dashboard", href: "/student/dashboard" },
  { label: "Resume", href: "/student/resume" },
  { label: "Analysis", href: "/student/analysis" },
  { label: "Profile", href: "/student/profile" },
];

export const facultyNavigation: NavItem[] = [
  { label: "Dashboard", href: "/faculty/dashboard" },
  { label: "Profile", href: "/faculty/profile" },
];

export const adminNavigation: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard" },
  { label: "Users", href: "/admin/users" },
  { label: "Resumes", href: "/admin/resumes" },
  { label: "Profile", href: "/admin/profile" },
];
