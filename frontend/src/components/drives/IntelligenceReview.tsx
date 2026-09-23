import React from "react";
import { CheckCircle2, AlertTriangle, Lightbulb, User, Star } from "lucide-react";

interface IntelligenceReviewProps {
  snapshot: any; // Using any for now, refine type as needed
}

export default function IntelligenceReview({ snapshot }: IntelligenceReviewProps) {
  const payload = snapshot?.intelligence_payload || {};
  const technologies = payload.technologies || [];
  const techCompetencies = payload.technical_competencies || [];
  const behaviors = payload.behavioral_competencies || [];
  const signals = payload.hiring_signals || [];
  const risks = payload.risks || [];

  return (
    <div className="space-y-8 bg-white p-6 md:p-8 rounded-xl border border-slate-200 shadow-sm">
      <div className="border-b border-slate-100 pb-5">
        <h2 className="text-xl font-bold text-slate-900">Intelligence Review</h2>
        <p className="text-sm text-slate-500 mt-1">Review the generated intelligence profile before publishing this drive.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Technologies */}
        <section>
          <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2 mb-4">
            <Star className="w-4 h-4 text-indigo-500" /> Required Technologies
          </h3>
          {technologies.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {technologies.map((tech: any, i: number) => (
                <span key={i} className="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded border border-indigo-100">
                  {tech.name} {tech.importance === 'CRITICAL' && '★'}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic">No technologies identified.</p>
          )}
        </section>

        {/* Competencies */}
        <section>
          <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Technical Competencies
          </h3>
          {techCompetencies.length > 0 ? (
            <ul className="space-y-2">
              {techCompetencies.map((comp: any, i: number) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-1.5 shrink-0" />
                  <span>{comp.name || comp.description}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400 italic">No technical competencies identified.</p>
          )}
        </section>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t border-slate-100">
        {/* Behavioral */}
        <section>
          <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2 mb-4">
            <User className="w-4 h-4 text-blue-500" /> Behavioral & Soft Skills
          </h3>
          {behaviors.length > 0 ? (
            <ul className="space-y-2">
              {behaviors.map((beh: any, i: number) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-1.5 shrink-0" />
                  <span>{beh.name || beh.description}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400 italic">No behavioral competencies identified.</p>
          )}
        </section>

        {/* Hiring Signals */}
        <section>
          <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2 mb-4">
            <Lightbulb className="w-4 h-4 text-amber-500" /> Hiring Signals
          </h3>
          {signals.length > 0 ? (
            <ul className="space-y-2">
              {signals.map((sig: any, i: number) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-amber-400 rounded-full mt-1.5 shrink-0" />
                  <span>{sig.signal || sig.description}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400 italic">No specific hiring signals identified.</p>
          )}
        </section>
      </div>

      {risks.length > 0 && (
        <div className="pt-6 border-t border-slate-100">
          <section className="bg-red-50 rounded-lg p-4 border border-red-100">
            <h3 className="text-md font-semibold text-red-800 flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-red-600" /> Risk Intelligence
            </h3>
            <ul className="space-y-2">
              {risks.map((risk: any, i: number) => (
                <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                  <span>•</span>
                  <span>{risk.description || risk.risk}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
