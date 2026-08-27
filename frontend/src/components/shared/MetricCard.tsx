import React from "react";
import Card from "./Card";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  subtitle?: string;
}

export default function MetricCard({ title, value, icon, subtitle }: MetricCardProps) {
  return (
    <Card className="p-6 flex flex-col justify-between h-full bg-white border border-slate-200 rounded-2xl shadow-sm">
      <div className="flex items-start justify-between">
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{title}</h3>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div className="mt-4">
        <span className="text-3xl font-bold text-slate-900">{value}</span>
        {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
      </div>
    </Card>
  );
}
