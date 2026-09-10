// All five endpoints here are REAL, confirmed, bare paths from the backend developer report
// (Section 4 of the authentication plan). No /auth prefix. No mocked responses anywhere below.

import { apiRequest } from "../lib/api";
import type {
  SignupPayload,
  SignupResponse,
  LoginPayload,
  LoginResponse,
  CurrentUser,
  ForgotPasswordPayload,
  GenericSuccessResponse,
  ResetPasswordPayload,
} from "../types/auth";

export const authService = {
  // POST /signup — real backend. Returns {success, message} only — NO token.
  signup(payload: SignupPayload): Promise<SignupResponse> {
    return apiRequest<SignupResponse>("/signup", { method: "POST", body: payload });
  },

  // POST /login — real backend. Email + password only (username login is not supported,
  // confirmed with backend team — do not add a username field here).
  login(payload: LoginPayload): Promise<LoginResponse> {
    return apiRequest<LoginResponse>("/login", { method: "POST", body: payload });
  },

  // GET /me — requires a real Bearer access_token.
  me(token: string): Promise<CurrentUser> {
    return apiRequest<CurrentUser>("/me", { method: "GET", token });
  },

  // POST /forgot-password — real backend. Always returns the same generic message
  // regardless of whether the account exists; do not branch UI copy on the response.
  forgotPassword(payload: ForgotPasswordPayload): Promise<GenericSuccessResponse> {
    return apiRequest<GenericSuccessResponse>("/forgot-password", { method: "POST", body: payload });
  },

  // POST /reset-password — real backend. token comes from the URL query string on the
  // Reset Password page (?token=...), not typed in by the user.
  resetPassword(payload: ResetPasswordPayload): Promise<GenericSuccessResponse> {
    return apiRequest<GenericSuccessResponse>("/reset-password", { method: "POST", body: payload });
  },
};
