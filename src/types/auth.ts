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
  email: string;
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

// Shape of FastAPI/Pydantic error bodies we actually need to handle.
export interface ApiErrorBody {
  detail?: string | { msg: string; loc?: (string | number)[] }[];
}
