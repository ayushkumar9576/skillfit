import React from "react";
import SelectionFunnelStepper from "./SelectionFunnelStepper";
import KeyEvaluationFocusBanner from "./KeyEvaluationFocusBanner";
import PriorityPreparationList from "./PriorityPreparationList";

export default function SelectionAndPreparationTab() {
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <SelectionFunnelStepper />
      <KeyEvaluationFocusBanner />
      <PriorityPreparationList />
    </div>
  );
}
