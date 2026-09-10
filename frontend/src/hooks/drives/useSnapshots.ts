import { useQuery } from "@tanstack/react-query";
import { getLatestSnapshot, getSnapshot, getSnapshotHistory } from "@/services/drives/snapshotService";
import { SnapshotDetailResponse, SnapshotListResponse } from "@/types/drives";

export const useLatestSnapshot = (driveId: string) => {
  return useQuery<SnapshotDetailResponse, Error>({
    queryKey: ["snapshot", driveId, "latest"],
    queryFn: () => getLatestSnapshot(driveId),
    staleTime: Infinity,
    enabled: !!driveId,
    retry: (failureCount, error: any) => {
      // Don't retry if it's a 404 (meaning no snapshot exists yet)
      if (error?.response?.status === 404) return false;
      return failureCount < 3;
    },
  });
};

export const useSnapshot = (driveId: string, snapshotId: string | null) => {
  return useQuery<SnapshotDetailResponse, Error>({
    queryKey: ["snapshot", driveId, snapshotId],
    queryFn: () => getSnapshot(driveId, snapshotId!),
    staleTime: Infinity,
    enabled: !!driveId && !!snapshotId && snapshotId !== "latest",
  });
};

export const useSnapshotHistory = (driveId: string) => {
  return useQuery<SnapshotListResponse, Error>({
    queryKey: ["snapshots", driveId],
    queryFn: () => getSnapshotHistory(driveId),
    staleTime: 60 * 1000, // 60 seconds
    enabled: !!driveId,
  });
};
