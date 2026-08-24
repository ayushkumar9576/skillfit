/**
 * app/(protected)/dashboard/page.tsx
 * ------------------------------------
 * Main dashboard overview page (/dashboard).
 * Composes all dashboard widgets.
 */

import WelcomeSection from "@/components/dashboard/WelcomeSection";
import ProfileCard from "@/components/dashboard/ProfileCard";
import ConnectivityStatus from "@/components/dashboard/ConnectivityStatus";
import RoadmapTimeline from "@/components/dashboard/RoadmapTimeline";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — SkillFit",
  description: "Your SkillFit placement intelligence dashboard.",
};

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {/* Welcome */}
      <WelcomeSection />

      {/* Main grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Profile — takes 1 column */}
        <div className="lg:col-span-1">
          <ProfileCard />
        </div>

        {/* Connectivity Status — takes 2 columns */}
        <div className="lg:col-span-2">
          <ConnectivityStatus />
        </div>
      </div>

      {/* Roadmap — full width */}
      <RoadmapTimeline />
    </div>
  );
}
