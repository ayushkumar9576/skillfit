import { cn } from "@/lib/utils";

type StatusType = "uploaded" | "processing" | "completed" | "failed";

interface StatusBadgeProps {
  status: StatusType;
  className?: string;
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = {
    uploaded: { label: "Uploaded", colors: "bg-slate-100 text-slate-700 border-slate-200" },
    processing: { label: "Processing", colors: "bg-amber-50 text-amber-700 border-amber-200" },
    completed: { label: "Completed", colors: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    failed: { label: "Failed", colors: "bg-red-50 text-red-700 border-red-200" },
  };

  const { label, colors } = config[status] || config.uploaded;

  return (
    <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold", colors, className)}>
      {label}
    </span>
  );
}
