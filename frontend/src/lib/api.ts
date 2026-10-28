import apiClient from "./api/client";

export async function fetchApi(url: string, options: RequestInit = {}) {
  const method = options.method || "GET";
  
  try {
    const response = await apiClient({
      url,
      method,
      data: options.body ? JSON.parse(options.body as string) : undefined,
      headers: options.headers as any,
    });
    
    return response.data;
  } catch (error: any) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      throw new Error(error.response.data.detail || error.response.data.message || "An error occurred");
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error("No response received from server");
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error(error.message);
    }
  }
}
