import apiClient from "./api/client";
import axios, { type RawAxiosRequestHeaders } from "axios";

function toAxiosHeaders(headers?: HeadersInit): RawAxiosRequestHeaders | undefined {
  if (!headers) return undefined;
  if (headers instanceof Headers) {
    const result: Record<string, string> = {};
    headers.forEach((value, key) => {
      result[key] = value;
    });
    return result;
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(headers);
  }
  return headers as RawAxiosRequestHeaders;
}

export async function fetchApi<T>(url: string, options: RequestInit = {}) {
  const method = options.method || "GET";
  
  try {
    const response = await apiClient<T>({
      url,
      method,
      data: options.body ? JSON.parse(options.body as string) : undefined,
      headers: toAxiosHeaders(options.headers),
    });
    
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const data = error.response.data as { detail?: string; message?: string } | undefined;
        throw new Error(data?.detail || data?.message || "An error occurred");
      } else if (error.request) {
        // The request was made but no response was received
        throw new Error("No response received from server");
      } else {
        // Something happened in setting up the request that triggered an Error
        throw new Error(error.message);
      }
    }
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("An unexpected error occurred");
  }
}
