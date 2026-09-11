import React, { createContext, useContext, useState, ReactNode } from "react";
import { Evidence } from "@/types/drives";

interface EvidenceContextState {
  isOpen: boolean;
  evidenceList: Evidence[];
  title: string;
}

interface EvidenceContextValue {
  openEvidence: (evidence: Evidence[], title?: string) => void;
  closeEvidence: () => void;
  state: EvidenceContextState;
}

const EvidenceContext = createContext<EvidenceContextValue | undefined>(undefined);

export function EvidenceProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<EvidenceContextState>({
    isOpen: false,
    evidenceList: [],
    title: "Supporting Evidence"
  });

  const openEvidence = (evidence: Evidence[], title = "Supporting Evidence") => {
    setState({ isOpen: true, evidenceList: evidence, title });
  };

  const closeEvidence = () => {
    setState((prev) => ({ ...prev, isOpen: false }));
  };

  return (
    <EvidenceContext.Provider value={{ openEvidence, closeEvidence, state }}>
      {children}
    </EvidenceContext.Provider>
  );
}

export function useEvidence() {
  const context = useContext(EvidenceContext);
  if (context === undefined) {
    throw new Error("useEvidence must be used within an EvidenceProvider");
  }
  return context;
}
