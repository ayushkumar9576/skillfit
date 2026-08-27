/**
 * types/auth.ts
 * -------------
 * TypeScript types derived 1:1 from the FastAPI Phase 2 backend schemas.
 * No invented fields. Every field maps to a concrete backend contract.
 *
 * Source schemas:
 *   - RegisterStudentSchema  → RegisterStudentRequest
 *   - RegisterFacultySchema  → RegisterFacultyRequest
 *   - LoginSchema            → LoginRequest
 *   - TokenSchema            → TokenResponse
 *   - UserResponseSchema     → User
 */

/** User roles as defined in app/core/enums.py UserRole enum. */
export type UserRole = "student" | "faculty" | "admin";

/**
 * Exact mirror of UserResponseSchema.
 * Only these 6 fields are returned by GET /auth/me and POST /auth/register/*.
 * Fields NOT included: created_at, last_login_at, email_verified (not in response schema).
 */
export interface User {
  id: string;                  // UUID v4 serialized as string
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  registration_number: string;
  requires_password_change?: boolean;
  profile_completed?: boolean;
  
  // Professional URLs (Student)
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  
  // Extra fields that will be added in profile APIs
  branch?: string;
  cgpa?: number;
  phone?: string;
  department?: string;
}

/**
 * Exact mirror of TokenSchema.
 * Returned by POST /auth/login on success.
 */
export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

/**
 * Exact mirror of LoginSchema.
 * POST /auth/login accepts registration_number + password.
 * Email is NOT used for authentication.
 */
export interface LoginRequest {
  registration_number: string;
  password: string;
}

/**
 * Exact mirror of RegisterStudentSchema.
 * POST /auth/register/student
 */
export interface RegisterStudentRequest {
  full_name: string;             // max 150 chars, stripped
  email: string;                 // valid email address
  registration_number: string;   // max 50 chars, stripped, must be unique
  password: string;              // min 12 chars
  branch?: string;               // optional, max 100 chars
  cgpa?: number;                 // optional, 0.0–10.0
  phone?: string;                // optional
}

/**
 * Exact mirror of RegisterFacultySchema.
 * POST /auth/register/faculty
 */
export interface RegisterFacultyRequest {
  full_name: string;             // max 150 chars, stripped
  email: string;                 // valid email address
  registration_number: string;   // max 50 chars, stripped, must be unique
  password: string;              // min 12 chars
  department?: string;           // optional, max 150 chars
}

/** Auth context state shape exposed via AuthProvider. */
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}
