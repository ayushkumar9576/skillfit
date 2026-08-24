/**
 * types/api.ts
 * ------------
 * Generic API response and error types for the SkillFit frontend.
 */

/** Shape of a FastAPI validation error item (HTTP 422). */
export interface ValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/** Shape of FastAPI's JSON error response body. */
export interface ApiErrorResponse {
  detail: string | ValidationErrorItem[];
}

/** Parsed, normalized error ready for display in the UI. */
export interface ParsedApiError {
  message: string;
  fieldErrors?: Record<string, string>;
}
