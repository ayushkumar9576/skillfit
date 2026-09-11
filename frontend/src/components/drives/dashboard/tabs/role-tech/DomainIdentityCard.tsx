import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import { Briefcase, Building, Layers, Component } from "lucide-react";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";

export default function DomainIdentityCard() {
  const { snapshot } = useDriveSnapshot();
  const domainData = snapshot?.intelligence_payload?.domain;

  if (!domainData) {
    return (
      <div className="h-full">
        <EmptyIntelligenceCard
          title="No Domain Identity Identified"
          description="The intelligence engine did not detect specific professional domains or subdomains for this role."
          icon={Briefcase}
        />
      </div>
    );
  }

  const formatEnumString = (str: string) => str.replace(/_/g, " ").toLowerCase();

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-indigo-500" />
          <h3 className="font-semibold text-slate-800">Domain Identity</h3>
        </div>
        <EvidenceTrigger evidence={domainData.evidence} title="Domain Evidence" />
      </div>

      <div className="p-5 flex-1 flex flex-col gap-6">
        {/* Core Domains */}
        <div className="flex flex-wrap gap-4">
          <div className="flex flex-col gap-1.5 flex-1 min-w-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Component className="h-3 w-3" />
              Professional Domain
            </span>
            <span className="text-lg font-medium text-slate-800 capitalize">
              {formatEnumString(domainData.domain)}
            </span>
          </div>

          {domainData.industry && (
            <div className="flex flex-col gap-1.5 flex-1 min-w-[140px]">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Building className="h-3 w-3" />
                Industry Vertical
              </span>
              <span className="text-lg font-medium text-slate-800 capitalize">
                {formatEnumString(domainData.industry)}
              </span>
            </div>
          )}
        </div>

        {/* Subdomains & Role Family */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          {domainData.role_family && (
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-2">Role Family</span>
              <span className="inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium bg-blue-50 text-blue-700 border border-blue-100">
                {domainData.role_family}
              </span>
            </div>
          )}

          {domainData.subdomains && domainData.subdomains.length > 0 && (
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5 mb-2">
                <Layers className="h-3 w-3" />
                Subdomains
              </span>
              <div className="flex flex-wrap gap-2">
                {domainData.subdomains.map((subdomain, idx) => (
                  <span
                    key={idx}
                    className="inline-flex px-2.5 py-1 rounded-md text-sm font-medium bg-slate-50 text-slate-700 border border-slate-200"
                  >
                    {subdomain}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
