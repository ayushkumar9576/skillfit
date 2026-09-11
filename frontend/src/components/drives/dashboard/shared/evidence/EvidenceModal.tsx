import React, { useEffect, useRef } from "react";
import { X, Search } from "lucide-react";
import { useEvidence } from "./EvidenceContext";

export default function EvidenceModal() {
  const { state, closeEvidence } = useEvidence();
  const { isOpen, evidenceList, title } = state;
  const modalRef = useRef<HTMLDivElement>(null);

  // Focus trap & ESC handling
  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeEvidence();
      
      // Strict focus trap
      if (e.key === "Tab" && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        ) as NodeListOf<HTMLElement>;
        
        if (focusableElements.length > 0) {
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };
    
    document.addEventListener("keydown", handleKeyDown);
    
    // Auto-focus first focusable element for accessibility
    const focusable = modalRef.current?.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])') as NodeListOf<HTMLElement>;
    if (focusable && focusable.length > 0) {
        focusable[0].focus();
    }

    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, closeEvidence]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-modal-title"
      onClick={closeEvidence}
    >
      <div 
        ref={modalRef}
        className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
        role="document"
        tabIndex={-1}
      >
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-indigo-100 text-indigo-600 rounded-md">
              <Search className="h-4 w-4" />
            </div>
            <h2 id="evidence-modal-title" className="text-lg font-semibold text-slate-800">
              {title}
            </h2>
          </div>
          <button 
            onClick={closeEvidence}
            className="text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-200 p-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Close evidence modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-0 overflow-y-auto flex-1">
          {evidenceList && evidenceList.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {evidenceList.map((item, idx) => (
                <li key={idx} className="p-6 flex flex-col gap-3 hover:bg-slate-50/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-1 rounded">
                      Source: {item.source_section.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded ${
                        item.evidence_type.includes("EXPLICIT") ? "text-slate-700 bg-slate-200" : "text-indigo-700 bg-indigo-100"
                      }`}>
                        {item.evidence_type.replace(/_/g, " ")}
                      </span>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded ${
                        item.confidence === "HIGH" ? "text-emerald-700 bg-emerald-100" :
                        item.confidence === "MEDIUM" ? "text-amber-700 bg-amber-100" :
                        "text-rose-700 bg-rose-100"
                      }`}>
                        {item.confidence} Confidence
                      </span>
                    </div>
                  </div>
                  <blockquote className="text-base text-slate-700 italic border-l-4 border-indigo-200 pl-4 py-1 leading-relaxed bg-slate-50/50 rounded-r-lg">
                    "{item.source_text}"
                  </blockquote>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-12 text-center text-slate-500">
              <Search className="h-10 w-10 text-slate-200 mx-auto mb-3" />
              <p className="font-medium text-slate-600">No specific evidence quotes available.</p>
              <p className="text-sm mt-1">The intelligence engine generated this insight without a direct quote.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
