/**
 * lib/api/auth.ts
 * ---------------
 * API call functions for Phase 2 authentication endpoints.
 * Only the 4 implemented backend endpoints are called here.
 */

import apiClient from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";
import type {
  LoginRequest,
  RegisterFacultyRequest,
  RegisterStudentRequest,
  TokenResponse,
  User,
} from "@/types/auth";

/**
 * Register a new student account.
 * POST /auth/register/student
 * Returns the created user's identity (UserResponseSchema).
 */
export async function registerStudent(data: RegisterStudentRequest): Promise<User> {
  const response = await apiClient.post<User>(ENDPOINTS.AUTH_REGISTER_STUDENT, data);
  return response.data;
}

/**
 * Register a new faculty account.
 * POST /auth/register/faculty
 * Returns the created user's identity (UserResponseSchema).
 */
export async function registerFaculty(data: RegisterFacultyRequest): Promise<User> {
  const response = await apiClient.post<User>(ENDPOINTS.AUTH_REGISTER_FACULTY, data);
  return response.data;
}

/**
 * Authenticate a user with registration_number + password.
 * POST /auth/login
 * Returns a JWT access token (TokenSchema).
 */
export async function loginUser(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(ENDPOINTS.AUTH_LOGIN, data);
  return response.data;
}

/**
 * Fetch the currently authenticated user's identity.
 * GET /auth/me
 * Requires a valid Bearer token in localStorage (injected by client interceptor).
 * Returns the user's identity (UserResponseSchema).
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>(ENDPOINTS.AUTH_ME);
  return response.data;
}

/**
 * Change the user's password.
 * POST /auth/change-password
 */
export async function changePassword(data: Record<string, unknown>): Promise<void> {
  await apiClient.post(ENDPOINTS.AUTH_CHANGE_PASSWORD, data);
}
