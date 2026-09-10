import apiClient from "@/lib/api/client";
import { DriveResponse, DriveListResponse } from "@/types/drives";

const BASE_URL = "/api/v1/drives";

export const getDrive = async (id: string): Promise<DriveResponse> => {
  const { data } = await apiClient.get<DriveResponse>(`${BASE_URL}/${id}`);
  return data;
};

export const updateDrive = async (
  id: string,
  payload: Partial<DriveResponse>
): Promise<DriveResponse> => {
  const { data } = await apiClient.patch<DriveResponse>(`${BASE_URL}/${id}`, payload);
  return data;
};

export const publishDrive = async (id: string): Promise<DriveResponse> => {
  // A helper function abstracting the state transition to published.
  // Assumes the backend accepts a partial update for status.
  const { data } = await apiClient.patch<DriveResponse>(`${BASE_URL}/${id}`, {
    status: "published",
  });
  return data;
};
