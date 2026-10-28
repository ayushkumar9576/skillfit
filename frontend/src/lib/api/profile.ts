import apiClient from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";
import type { User } from "@/types/auth";

export async function updateProfile(data: Record<string, unknown>): Promise<User> {
  const response = await apiClient.put<User>(ENDPOINTS.PROFILE_UPDATE, data);
  return response.data;
}
