import React from "react";
import { X } from "lucide-react";
import { Evidence } from "@/types/drives";

interface EvidencePopoverProps {
  evidence: Evidence[];
  isOpen: boolean;
  onClose: () => void;
  title?: string;
}

export default function EvidencePopover({ evidence, isOpen, onClose, title = "Supporting Evidence" }: EvidencePopoverProps) {
  if (!isOpen) return null;

  return (
    <div className="absolute z-50 left-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-100">
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <button 
          onClick={(e) => { e.stopPropagation(); onClose(); }}
          className="text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-200 p-1 transition-colors"
          aria-label="Close evidence"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="p-0 max-h-64 overflow-y-auto">
        {evidence && evidence.length > 0 ? (
          <ul className="divide-y divide-slate-100">
            {evidence.map((item, idx) => (
              <li key={idx} className="p-4 flex flex-col gap-2 hover:bg-slate-50/50 transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    {item.source_section.replace(/_/g, " ")}
                  </span>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    item.evidence_type.includes("EXPLICIT") ? "text-slate-600 bg-slate-100" : "text-indigo-600 bg-indigo-50"
                  }`}>
                    {item.evidence_type.replace(/_/g, " ")}
                  </span>
                </div>
                <blockquote className="text-sm text-slate-700 italic border-l-2 border-indigo-200 pl-3 py-0.5">
                  "{item.source_text}"
                </blockquote>
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-6 text-center text-sm text-slate-500">
            No specific evidence quotes available.
          </div>
        )}
      </div>
    </div>
  );
}
