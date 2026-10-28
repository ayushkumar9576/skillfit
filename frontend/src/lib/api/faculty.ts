import apiClient from "./client";

export interface FacultyDashboardData {
  profile_completed: boolean;
  department: string | null;
}

export const getFacultyDashboard = async (): Promise<FacultyDashboardData> => {
  const { data } = await apiClient.get<FacultyDashboardData>("/api/v1/faculty/dashboard");
  return data;
};
