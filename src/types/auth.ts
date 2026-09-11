// Types mirror the REAL backend contract from the confirmed backend developer report.
// No speculative fields — only what /signup, /login, and /me actually send/return.

export interface SignupPayload {
  username: string;
  email: string;
  create_password: string;
  confirm_password: string;
}

export interface SignupResponse {
  success: boolean;
  message: string;
  // NOTE: backend does NOT return a token on signup. Do not add access_token here —
  // if it's ever added, update this type only after the backend teammate confirms it.
}

export interface LoginPayload {
  // Backend's real LoginRequest field is `identifier` (email OR username),
  // not `email` — confirmed against app/schemas/user.py. Keeping the field
  // name aligned with the backend contract so this doesn't silently 422.
  identifier: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  access_token: string;
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  email_verified: boolean;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface GenericSuccessResponse {
  success: boolean;
  message: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface VerifyEmailPayload {
  token: string;
}

export interface ResendVerificationPayload {
  email: string;
}

export interface DeleteAccountPayload {
  password: string;
}

export interface CheckUsernameResponse {
  available: boolean;
  suggestions?: string[];
}

// Shape of FastAPI/Pydantic error bodies we actually need to handle.
export interface ApiErrorBody {
  detail?: string | { msg: string; loc?: (string | number)[] }[];
}
