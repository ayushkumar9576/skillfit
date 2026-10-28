import apiClient from "./client";

export interface DimensionBreakdown {
  dimension: string;
  raw_score: number;
  weight: number;
  weighted_score: number;
  matched_items: number;
  total_items: number;
  reasoning: string;
  strengths: string[];
  gaps: string[];
}

export interface RecommendedDrive {
  drive_id: string;
  drive_title: string;
  company_name: string | null;
  score: number;
  raw_score?: number;
  tier: string;
  strengths: string[];
  gaps: string[];
  overall_narrative: string;
  dimension_breakdown?: DimensionBreakdown[];
}

export interface RecommendedCandidate {
  candidate_id: string;
  student_name: string;
  score: number;
  raw_score?: number;
  tier: string;
  strengths: string[];
  gaps: string[];
  overall_narrative: string;
  dimension_breakdown?: DimensionBreakdown[];
}

export const getRecommendedDrives = async (): Promise<RecommendedDrive[]> => {
  const { data } = await apiClient.get(`/api/v1/students/me/recommended-drives`);
  return data;
};

export const getRecommendedCandidates = async (driveId: string): Promise<RecommendedCandidate[]> => {
  const { data } = await apiClient.get(`/api/v1/drives/${driveId}/recommended-candidates`);
  return data;
};
