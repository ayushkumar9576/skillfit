import React from "react";
import LoadingState from "./LoadingState";
import EmptyState from "./EmptyState";
import { LucideIcon } from "lucide-react";

interface Column<T> {
  header: string;
  accessor: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  isLoading?: boolean;
  emptyIcon: LucideIcon;
  emptyTitle?: string;
  emptyDescription: string;
  emptyAction?: React.ReactNode;
}

export default function DataTable<T>({ 
  data, 
  columns, 
  isLoading,
  emptyIcon,
  emptyTitle = "No data available",
  emptyDescription,
  emptyAction
}: DataTableProps<T>) {
  if (isLoading) {
    return <LoadingState message="Loading data..." className="py-12" />;
  }

  if (data.length === 0) {
    return (
      <div className="py-12 border border-slate-200 rounded-xl bg-white shadow-sm">
        <EmptyState 
          icon={emptyIcon}
          title={emptyTitle}
          description={emptyDescription}
          action={emptyAction}
        />
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full text-left text-sm text-slate-600">
        <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
          <tr>
            {columns.map((col, i) => (
              <th key={i} scope="col" className={`px-6 py-4 font-semibold ${col.className || ""}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="bg-white hover:bg-slate-50/50 transition-colors">
              {columns.map((col, colIndex) => (
                <td key={colIndex} className={`px-6 py-4 whitespace-nowrap ${col.className || ""}`}>
                  {col.accessor(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
