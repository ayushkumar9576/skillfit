/**
 * lib/api/endpoints.ts
 * --------------------
 * Centralized API endpoint path constants.
 * Only endpoints that have been implemented in the backend are listed here.
 */

export const ENDPOINTS = {
  /** POST /auth/register/student — Creates a new student account */
  AUTH_REGISTER_STUDENT: "/auth/register/student",

  /** POST /auth/register/faculty — Creates a new faculty account */
  AUTH_REGISTER_FACULTY: "/auth/register/faculty",

  /** POST /auth/login — Authenticates via registration_number + password, returns JWT */
  AUTH_LOGIN: "/auth/login",

  /** GET /auth/me — Returns the current authenticated user's identity */
  AUTH_ME: "/auth/me",

  /** GET /health — Backend health check */
  HEALTH: "/health",

  /** POST /auth/change-password — Changes temporary password */
  AUTH_CHANGE_PASSWORD: "/auth/change-password",

  /** PUT /api/v1/profile — Updates user profile details */
  PROFILE_UPDATE: "/api/v1/profile",

  /** Base route for all resume operations (upload, list, analysis) */
  RESUMES_BASE: "/api/v1/resumes",

  /** GET /api/v1/student/dashboard — Fetches student dashboard */
  DASHBOARD_STUDENT: "/api/v1/student/dashboard",

  /** GET /api/v1/faculty/dashboard — Fetches faculty dashboard */
  DASHBOARD_FACULTY: "/api/v1/faculty/dashboard",

  /** GET /api/v1/admin/dashboard — Fetches admin dashboard */
  DASHBOARD_ADMIN: "/api/v1/admin/dashboard",
} as const;
