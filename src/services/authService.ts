// Every endpoint below is a REAL, confirmed, bare path against app/main.py on the backend.
// No /auth prefix. No mocked responses anywhere below.

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
  VerifyEmailPayload,
  ResendVerificationPayload,
  DeleteAccountPayload,
  CheckUsernameResponse,
} from "../types/auth";

export const authService = {
  // POST /signup — real backend. Returns {success, message} only — NO token.
  // With REQUIRE_EMAIL_VERIFICATION on (the backend default), the new account
  // cannot log in until the emailed link is clicked, so callers should NOT
  // assume an auto-login will succeed right after this resolves.
  signup(payload: SignupPayload): Promise<SignupResponse> {
    return apiRequest<SignupResponse>("/signup", { method: "POST", body: payload });
  },

  // POST /login — real backend. Body field is `identifier` (accepts EITHER the
  // account's email or its username — confirmed against LoginRequest in
  // app/schemas/user.py). Can reject with 403 (email not verified yet) or
  // 423 (account temporarily locked after too many failed attempts).
  login(payload: LoginPayload): Promise<LoginResponse> {
    return apiRequest<LoginResponse>("/login", { method: "POST", body: payload });
  },

  // GET /me — requires a real Bearer access_token.
  me(token: string): Promise<CurrentUser> {
    return apiRequest<CurrentUser>("/me", { method: "GET", token });
  },

  // POST /logout — real backend. Requires Bearer token, no body. Bumps the user's
  // token_version server-side, invalidating the current token immediately.
  logout(token: string): Promise<GenericSuccessResponse> {
    return apiRequest<GenericSuccessResponse>("/logout", { method: "POST", token });
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

  // POST /verify-email — real backend. token comes from the URL query string on the
  // Verify Email page (?token=...), which is exactly what the signup email links to.
  verifyEmail(payload: VerifyEmailPayload): Promise<GenericSuccessResponse> {
    return apiRequest<GenericSuccessResponse>("/verify-email", { method: "POST", body: payload });
  },

  // POST /resend-verification-email — real backend. Always returns the same generic
  // message regardless of whether the account exists or is already verified.
  resendVerificationEmail(payload: ResendVerificationPayload): Promise<GenericSuccessResponse> {
    return apiRequest<GenericSuccessResponse>("/resend-verification-email", {
      method: "POST",
      body: payload,
    });
  },

  // POST /delete-account — real backend. Requires Bearer token AND the current
  // password as confirmation. Permanently deletes the account server-side.
  deleteAccount(payload: DeleteAccountPayload, token: string): Promise<GenericSuccessResponse> {
    return apiRequest<GenericSuccessResponse>("/delete-account", {
      method: "POST",
      body: payload,
      token,
    });
  },

  // GET /check-username?username=... — real backend, read-only, debounced on the
  // frontend. Response omits `suggestions` entirely when the name is available
  // (response_model_exclude_none on the route), so treat it as optional.
  checkUsername(username: string): Promise<CheckUsernameResponse> {
    return apiRequest<CheckUsernameResponse>(
      `/check-username?username=${encodeURIComponent(username)}`,
      { method: "GET" }
    );
  },
};
