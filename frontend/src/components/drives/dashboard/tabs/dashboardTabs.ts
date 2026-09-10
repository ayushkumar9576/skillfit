export interface DashboardTab {
  id: string;
  label: string;
  icon?: string;
}

export const DASHBOARD_TABS: DashboardTab[] = [
  {
    id: "role-tech",
    label: "Role & Tech Stack",
  },
  {
    id: "eligibility",
    label: "Eligibility & Terms",
  },
  {
    id: "selection",
    label: "Selection & Prep",
  },
  {
    id: "evaluation",
    label: "Evaluation & Culture",
  },
  {
    id: "audit",
    label: "JD & Audit",
  },
];
