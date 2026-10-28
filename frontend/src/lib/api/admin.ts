import apiClient from "./client";
import type { User } from "@/types/auth";

export interface AdminDashboardData {
  total_students: number;
  total_faculty: number;
  uploaded_resumes: number;
  processing_resumes: number;
  completed_resumes: number;
  failed_resumes: number;
}

export interface QueueSummary {
  uploaded: number;
  processing: number;
  completed: number;
  failed: number;
}

export interface PendingResume {
  resume_id: string;
  student_id: string;
  student_name: string;
  resume_type: "generic" | "specialized";
  processing_status: "uploaded" | "processing" | "completed" | "failed";
  upload_date: string;
}

export interface PendingQueueResponse {
  items: PendingResume[];
  total: number;
}

export const getAdminDashboard = async (): Promise<AdminDashboardData> => {
  const { data } = await apiClient.get<AdminDashboardData>("/api/v1/admin/dashboard");
  return data;
};

export const getQueueSummary = async (): Promise<QueueSummary> => {
  const { data } = await apiClient.get<QueueSummary>("/api/v1/admin/resumes/queue-summary");
  return data;
};

export const getPendingResumes = async (skip = 0, limit = 50): Promise<PendingQueueResponse> => {
  const { data } = await apiClient.get<PendingQueueResponse>("/api/v1/admin/resumes/pending", {
    params: { skip, limit }
  });
  return data;
};

export const triggerAnalysis = async (resumeId: string): Promise<{ status: string, message: string }> => {
  const { data } = await apiClient.post(`/api/v1/admin/resumes/${resumeId}/analyze`);
  return data;
};

export const triggerBatchAnalysis = async (limit: number): Promise<Record<string, unknown>> => {
  const { data } = await apiClient.post("/api/v1/admin/resumes/analyze-batch", { limit });
  return data;
};

export const createStudent = async (payload: Record<string, unknown>): Promise<User> => {
  const { data } = await apiClient.post<User>("/api/v1/admin/users/student", payload);
  return data;
};

export const createFaculty = async (payload: Record<string, unknown>): Promise<User> => {
  const { data } = await apiClient.post<User>("/api/v1/admin/users/faculty", payload);
  return data;
};
