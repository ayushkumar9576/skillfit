"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { SnapshotDetailResponse } from "@/types/drives";

interface SnapshotContextValue {
  snapshot: SnapshotDetailResponse | null;
  selectedSnapshotId: string | null;
  setSelectedSnapshotId: (id: string | null) => void;
  isHistoricalView: boolean;
}

const SnapshotContext = createContext<SnapshotContextValue | undefined>(undefined);

export const SnapshotProvider: React.FC<{
  children: React.ReactNode;
  snapshot: SnapshotDetailResponse | null;
  initialSelectedSnapshotId?: string | null;
}> = ({ children, snapshot, initialSelectedSnapshotId = null }) => {
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(initialSelectedSnapshotId);

  // If the parent explicitly passes down a new snapshot, but we don't have a selection,
  // we default the historical view to false.
  const isHistoricalView = selectedSnapshotId !== null && selectedSnapshotId !== "latest";

  return (
    <SnapshotContext.Provider
      value={{
        snapshot,
        selectedSnapshotId,
        setSelectedSnapshotId,
        isHistoricalView,
      }}
    >
      {children}
    </SnapshotContext.Provider>
  );
};

export const useDriveSnapshot = (): SnapshotContextValue => {
  const context = useContext(SnapshotContext);
  if (context === undefined) {
    throw new Error("useDriveSnapshot must be used within a SnapshotProvider");
  }
  return context;
};
