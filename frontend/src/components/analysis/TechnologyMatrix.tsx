"use client";

import { useState, useMemo } from "react";
import { Cpu, Search, ArrowUpDown } from "lucide-react";
import StateWrapper from "./StateWrapper";
import type { TechnologyIntelligence } from "@/types/candidate-profile";
import DemonstrationLevelBadge from "@/components/shared/DemonstrationLevelBadge";
import EvidenceSourceBadge from "@/components/shared/EvidenceSourceBadge";
import { DemonstrationLevel } from "@/types/candidate-profile";

interface TechnologyMatrixProps {
  technologies: TechnologyIntelligence[];
  isLoading?: boolean;
  error?: Error | null;
}

type SortField = 'technology' | 'level' | 'evidence';
type SortOrder = 'asc' | 'desc';

const LEVEL_RANK: Record<string, number> = {
  'ARCHITECTED': 5,
  'DESIGNED': 4,
  'IMPLEMENTED': 3,
  'USED': 2,
  'REFERENCED': 1,
  'CLAIMED': 0
};

export default function TechnologyMatrix({
  technologies,
  isLoading = false,
  error = null,
}: TechnologyMatrixProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<SortField>('level');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const filteredAndSortedTechs = useMemo(() => {
    if (!technologies) return [];
    
    // Filter
    let result = technologies.filter(tech => 
      tech.technology.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'technology':
          comparison = a.technology.localeCompare(b.technology);
          break;
        case 'level':
          const rankA = LEVEL_RANK[a.demonstration_level] ?? -1;
          const rankB = LEVEL_RANK[b.demonstration_level] ?? -1;
          comparison = rankA - rankB;
          break;
        case 'evidence':
          comparison = (a.evidence?.length || 0) - (b.evidence?.length || 0);
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [technologies, searchTerm, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const SortButton = ({ field, label }: { field: SortField, label: string }) => (
    <button 
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 hover:text-slate-900 focus:outline-none"
    >
      {label}
      <ArrowUpDown className={`h-3 w-3 ${sortField === field ? 'text-indigo-600' : 'text-slate-400'}`} />
    </button>
  );

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!technologies || technologies.length === 0}
      emptyTitle="No Technologies Detected"
      emptyMessage="No programming languages, frameworks, or tools were found in the evidence."
    >
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="border-b border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Cpu className="h-5 w-5 text-indigo-500" />
              Technology Demonstration Matrix
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Verified skills and their corresponding demonstration level.
            </p>
          </div>
          
          <div className="relative w-full sm:w-64">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Search className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="text"
              placeholder="Search technologies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full rounded-md border-0 py-1.5 pl-9 pr-3 text-slate-900 ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <SortButton field="technology" label="Technology" />
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <SortButton field="level" label="Demonstration Level" />
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Sources
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <SortButton field="evidence" label="Evidence Count" />
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {filteredAndSortedTechs.map((tech) => (
                <tr key={tech.technology} className="hover:bg-slate-50 transition-colors">
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-slate-900">
                    {tech.technology}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <DemonstrationLevelBadge level={tech.demonstration_level} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-2">
                      {tech.source_types?.map(src => (
                        <EvidenceSourceBadge key={src} source={src} />
                      ))}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-500">
                    <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-slate-100 text-slate-700 font-medium">
                      {tech.evidence?.length || 0}
                    </span>
                  </td>
                </tr>
              ))}
              {filteredAndSortedTechs.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-sm text-slate-500">
                    No technologies match your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </StateWrapper>
  );
}
