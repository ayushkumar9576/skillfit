import apiClient from "@/lib/api/client";
import { SnapshotDetailResponse, SnapshotListResponse } from "@/types/drives";

const BASE_URL = "/api/v1/drives";

export const getLatestSnapshot = async (
  driveId: string
): Promise<SnapshotDetailResponse> => {
  const { data } = await apiClient.get<SnapshotDetailResponse>(
    `${BASE_URL}/${driveId}/snapshots/latest`
  );
  return data;
};

export const getSnapshot = async (
  driveId: string,
  snapshotId: string
): Promise<SnapshotDetailResponse> => {
  const { data } = await apiClient.get<SnapshotDetailResponse>(
    `${BASE_URL}/${driveId}/snapshots/${snapshotId}`
  );
  return data;
};

export const getSnapshotHistory = async (
  driveId: string
): Promise<SnapshotListResponse> => {
  const { data } = await apiClient.get<SnapshotListResponse>(
    `${BASE_URL}/${driveId}/snapshots`
  );
  return data;
};
