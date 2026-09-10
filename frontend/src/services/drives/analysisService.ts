import apiClient from "@/lib/api/client";
import { AnalyzeDriveRequest, AnalysisResponse, AnalysisListResponse } from "@/types/drives";

const BASE_URL = "/api/v1/drives";

export const triggerAnalysis = async (
  driveId: string,
  requestBody: AnalyzeDriveRequest = {}
): Promise<AnalysisResponse> => {
  const { data } = await apiClient.post<AnalysisResponse>(
    `${BASE_URL}/${driveId}/analyze`,
    requestBody
  );
  return data;
};

export const getAnalysisHistory = async (
  driveId: string,
  limit: number = 20
): Promise<AnalysisListResponse> => {
  const { data } = await apiClient.get<AnalysisListResponse>(
    `${BASE_URL}/${driveId}/analysis`,
    { params: { limit } }
  );
  return data;
};
