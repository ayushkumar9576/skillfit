import React, { useState } from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import { useEvidence } from "../../../shared/evidence/EvidenceContext";
import { Search, ChevronRight, Folder } from "lucide-react";

export default function EvidenceExplorer() {
  const { snapshot } = useDriveSnapshot();
  const { openEvidence } = useEvidence();
  const [activeCategory, setActiveCategory] = useState<string>("technologies");

  const categories = [
    { id: "technologies", label: "Technologies", count: snapshot?.intelligence_payload?.technologies?.length || 0 },
    { id: "technical_competencies", label: "Technical Competencies", count: snapshot?.intelligence_payload?.technical_competencies?.length || 0 },
    { id: "behavioral_competencies", label: "Behavioral Competencies", count: snapshot?.intelligence_payload?.behavioral_competencies?.length || 0 },
    { id: "qualifications", label: "Qualifications", count: snapshot?.intelligence_payload?.qualifications?.length || 0 },
    { id: "risks", label: "Risks", count: snapshot?.intelligence_payload?.risks?.length || 0 },
  ];

  const renderActiveCategoryContent = () => {
    if (!snapshot || !snapshot.intelligence_payload) return null;
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const items: any[] = (snapshot.intelligence_payload as any)[activeCategory] || [];

    if (items.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 py-12">
          <Search className="h-8 w-8 mb-2 opacity-50" />
          <p className="text-sm">No items in this category.</p>
        </div>
      );
    }

    return (
      <ul className="divide-y divide-slate-100 border-t border-slate-100">
        {items.map((item, idx) => {
          // Identify name field based on structure
          const name = item.name || item.competency || item.qualification_type || item.risk || `Item ${idx+1}`;
          const formattedName = typeof name === 'string' ? name.replace(/_/g, " ").toLowerCase() : name;
          const hasEvidence = item.evidence && item.evidence.length > 0;

          return (
            <li 
              key={idx} 
              className={`flex items-center justify-between p-3 transition-colors ${hasEvidence ? 'hover:bg-indigo-50 cursor-pointer group' : 'opacity-70'}`}
              onClick={() => hasEvidence && openEvidence(item.evidence, `Evidence for ${formattedName}`)}
            >
              <div className="flex items-center gap-3">
                <span className="capitalize text-sm font-medium text-slate-700 group-hover:text-indigo-700">{formattedName}</span>
              </div>
              {hasEvidence ? (
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-indigo-500 bg-indigo-100 px-1.5 py-0.5 rounded">{item.evidence.length} Quotes</span>
                  <ChevronRight className="h-4 w-4 text-indigo-300 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1" />
                </div>
              ) : (
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">No Quotes</span>
              )}
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden max-h-[600px]">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <Folder className="h-4 w-4 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Intelligence Evidence Explorer</h3>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-1/3 border-r border-slate-100 bg-slate-50/50 flex flex-col overflow-y-auto">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`flex items-center justify-between p-3 text-left transition-colors border-l-2 ${
                activeCategory === cat.id 
                  ? "bg-white border-indigo-500 text-indigo-700 shadow-sm" 
                  : "border-transparent text-slate-600 hover:bg-slate-100"
              }`}
            >
              <span className="text-xs font-semibold uppercase tracking-wider">{cat.label}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                activeCategory === cat.id ? "bg-indigo-100 text-indigo-700" : "bg-slate-200 text-slate-500"
              }`}>
                {cat.count}
              </span>
            </button>
          ))}
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {renderActiveCategoryContent()}
        </div>
      </div>
    </div>
  );
}
