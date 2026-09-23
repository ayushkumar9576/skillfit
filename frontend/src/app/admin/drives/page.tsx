import React from "react";
import Link from "next/link";
import { PlusCircle, Clock, CheckCircle2, Globe, ArrowRight } from "lucide-react";

const cards = [
  {
    title: "Create Drive",
    description: "Initialize a new placement drive and set up its metadata.",
    href: "/admin/drives/create",
    icon: PlusCircle,
    color: "bg-blue-50 text-blue-700",
  },
  {
    title: "Pending Analysis",
    description: "View and manage drives in draft, analyzing, or failed states.",
    href: "/admin/drives/pending",
    icon: Clock,
    color: "bg-amber-50 text-amber-700",
  },
  {
    title: "Awaiting Approval",
    description: "Review generated intelligence and approve drives for publication.",
    href: "/admin/drives/approvals",
    icon: CheckCircle2,
    color: "bg-purple-50 text-purple-700",
  },
  {
    title: "Published Drives",
    description: "Manage live placement drives visible to students.",
    href: "/admin/drives/published",
    icon: Globe,
    color: "bg-emerald-50 text-emerald-700",
  },
];

export default function DriveWorkspaceHome() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Workspace Home</h2>
        <p className="text-slate-500 mt-1">
          Manage the full lifecycle of placement drives from creation to publication.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.title}
              href={card.href}
              className="group block bg-white border border-slate-200 rounded-xl p-6 hover:shadow-md hover:border-indigo-300 transition-all duration-200"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${card.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                      {card.title}
                    </h3>
                    <p className="text-slate-500 text-sm mt-1">{card.description}</p>
                  </div>
                </div>
                <div className="text-slate-400 group-hover:text-indigo-600 transition-colors transform group-hover:translate-x-1">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
