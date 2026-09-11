import React, { memo } from "react";
import { PreparationTopic } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { BookOpen } from "lucide-react";

interface PreparationTopicCardProps {
  topic: PreparationTopic;
}

const PreparationTopicCard = memo(function PreparationTopicCard({ topic }: PreparationTopicCardProps) {
  const isCritical = topic.importance === "CRITICAL";

  return (
    <div className={`flex flex-col p-4 border rounded-xl shadow-sm transition-shadow hover:shadow-md bg-white ${
      isCritical ? "border-rose-200" : "border-slate-200"
    }`}>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${
            isCritical ? "bg-rose-100 text-rose-600" : "bg-indigo-100 text-indigo-600"
          }`}>
            <BookOpen className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <h4 className="font-semibold text-slate-800 text-base leading-tight">
              {topic.topic_name}
            </h4>
            <span className="text-xs font-medium text-slate-500 mt-0.5">
              Target: <span className="font-bold text-slate-700">{topic.target_round_type.replace(/_/g, " ")}</span>
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${
            isCritical ? 'bg-rose-100 text-rose-700' :
            topic.importance === "HIGH" ? 'bg-orange-100 text-orange-700' :
            'bg-slate-100 text-slate-700'
          }`}>
            {topic.importance} Importance
          </span>
          <EvidenceTrigger evidence={topic.evidence} title={`Evidence for ${topic.topic_name}`} />
        </div>
      </div>

      <div className="mt-auto bg-slate-50 p-3 rounded-lg border border-slate-100">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">Recommended Focus</span>
        <p className="text-sm text-slate-700 leading-snug">
          {topic.recommended_focus}
        </p>
      </div>
    </div>
  );
});

export default PreparationTopicCard;
