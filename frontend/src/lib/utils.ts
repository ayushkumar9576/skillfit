/**
 * lib/utils.ts
 * ------------
 * Shared utility functions for the SkillFit frontend.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { ParsedApiError } from "@/types/api";
import axios from "axios";

/** Merges Tailwind CSS class names safely, resolving conflicts. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Parses an Axios error into a user-friendly ParsedApiError.
 * Handles FastAPI's 422 validation errors, 401/403/409 errors,
 * and network-level failures.
 */
export function parseApiError(error: unknown): ParsedApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data;

    // FastAPI 422 Unprocessable Entity — Pydantic validation errors
    if (status === 422 && data?.detail && Array.isArray(data.detail)) {
      const fieldErrors: Record<string, string> = {};
      for (const item of data.detail) {
        const field = item.loc[item.loc.length - 1] as string;
        if (field) fieldErrors[field] = item.msg;
      }
      return {
        message: "Please fix the errors below.",
        fieldErrors,
      };
    }

    // FastAPI string detail errors (401, 403, 409, 429, etc.)
    if (data?.detail && typeof data.detail === "string") {
      return { message: data.detail };
    }

    // HTTP-level errors without a detail body
    if (status === 401) return { message: "Invalid credentials. Please check your registration number and password." };
    if (status === 403) return { message: "You do not have permission to perform this action." };
    if (status === 409) return { message: "An account with these details already exists." };
    if (status === 429) return { message: "Too many attempts. Please wait a few minutes and try again." };
    if (status && status >= 500) return { message: "Server error. Please try again later." };

    // Network error (backend unreachable)
    if (!error.response) {
      return { message: "Unable to connect to the server. Please check your connection and try again." };
    }
  }

  return { message: "Something went wrong. Please try again." };
}
