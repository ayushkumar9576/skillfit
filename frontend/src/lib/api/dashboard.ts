import apiClient from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";

export async function getStudentDashboard() {
  const response = await apiClient.get(ENDPOINTS.DASHBOARD_STUDENT);
  return response.data;
}

export async function getFacultyDashboard() {
  const response = await apiClient.get(ENDPOINTS.DASHBOARD_FACULTY);
  return response.data;
}

export async function getAdminDashboard() {
  const response = await apiClient.get(ENDPOINTS.DASHBOARD_ADMIN);
  return response.data;
}
