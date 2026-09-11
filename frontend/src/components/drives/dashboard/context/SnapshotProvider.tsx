"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { SnapshotDetailResponse } from "@/types/drives";

import { useSnapshot } from "@/hooks/drives/useSnapshots";

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
  driveId: string;
  initialSelectedSnapshotId?: string | null;
}> = ({ children, snapshot: latestSnapshot, driveId, initialSelectedSnapshotId = null }) => {
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(initialSelectedSnapshotId);

  // If the parent explicitly passes down a new snapshot, but we don't have a selection,
  // we default the historical view to false.
  const isHistoricalView = selectedSnapshotId !== null && selectedSnapshotId !== "latest";

  const { data: historicalSnapshot } = useSnapshot(driveId, isHistoricalView ? selectedSnapshotId : null);

  const currentSnapshot = isHistoricalView ? (historicalSnapshot || null) : latestSnapshot;

  return (
    <SnapshotContext.Provider
      value={{
        snapshot: currentSnapshot,
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
