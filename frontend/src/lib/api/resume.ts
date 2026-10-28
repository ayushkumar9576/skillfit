import apiClient from "./client";
import { ENDPOINTS } from "./endpoints";
import type { CandidateIntelligenceProfile } from "@/types/candidate-profile";

export interface ResumeFile {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  resume_type: "generic" | "specialized";
  processing_status: "uploaded" | "processing" | "completed" | "failed";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function uploadResume(file: File, resumeType: "generic" | "specialized"): Promise<ResumeFile> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("resume_type", resumeType);

  const response = await apiClient.post<ResumeFile>(ENDPOINTS.RESUMES_BASE, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export interface ResumeListResponse {
  resumes: ResumeFile[];
  total: number;
}

export async function getResumes(): Promise<ResumeListResponse> {
  const response = await apiClient.get<ResumeListResponse>(ENDPOINTS.RESUMES_BASE);
  return response.data;
}



export async function getCandidateProfile(id: string): Promise<CandidateIntelligenceProfile> {
  const response = await apiClient.get<CandidateIntelligenceProfile>(`${ENDPOINTS.RESUMES_BASE}/${id}/profile`);
  return response.data;
}
