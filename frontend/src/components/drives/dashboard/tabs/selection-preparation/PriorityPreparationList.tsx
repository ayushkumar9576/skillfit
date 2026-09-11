import React, { useMemo } from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import PreparationTopicCard from "./PreparationTopicCard";
import { BookOpen } from "lucide-react";

export default function PriorityPreparationList() {
  const { snapshot } = useDriveSnapshot();
  const topics = snapshot?.intelligence_payload?.preparation?.priority_topics;

  const sortedTopics = useMemo(() => {
    if (!topics) return [];
    
    const getWeight = (imp: string) => {
      switch (imp) {
        case "CRITICAL": return 4;
        case "HIGH": return 3;
        case "MEDIUM": return 2;
        case "LOW": return 1;
        default: return 0;
      }
    };

    return [...topics].sort((a, b) => getWeight(b.importance) - getWeight(a.importance));
  }, [topics]);

  if (!sortedTopics || sortedTopics.length === 0) {
    return (
      <div className="h-[300px]">
        <EmptyIntelligenceCard
          title="No Preparation Topics Found"
          description="Specific preparation advice or recommended focus areas were not identified for this drive."
          icon={BookOpen}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold text-slate-800 flex items-center gap-2 px-1">
        <BookOpen className="h-5 w-5 text-indigo-500" />
        Priority Preparation Topics
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {sortedTopics.map((topic, idx) => (
          <PreparationTopicCard key={`${topic.topic_name}-${idx}`} topic={topic} />
        ))}
      </div>
    </div>
  );
}
