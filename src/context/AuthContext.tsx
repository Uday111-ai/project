import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from "react";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";
import type { CurrentUser, SignupPayload, DeleteAccountPayload } from "../types/auth";

// Token storage decision (Section 8 of the plan): kept in memory (React state) only.
// This means a hard page refresh logs the user out — that's a deliberate, documented
// trade-off, not a bug. There is no backend refresh-token mechanism to restore a session
// against, and no HttpOnly cookie option from the backend, so memory is the safest default.
// If this trade-off changes, update this file and Section 8 together — don't drift apart.

interface AuthContextValue {
  user: CurrentUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  // Returns the backend's confirmation message so the caller (Signup page) can
  // show it — signup no longer auto-logs-in, since REQUIRE_EMAIL_VERIFICATION
  // is on by default and login will 403 until the emailed link is clicked.
  signup: (payload: SignupPayload) => Promise<string>;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  deleteAccount: (password: string) => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const hydrateUser = useCallback(async (token: string) => {
    const currentUser = await authService.me(token);
    setUser(currentUser);
  }, []);

  const login = useCallback(
    async (identifier: string, password: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await authService.login({ identifier, password });
        setAccessToken(res.access_token);
        await hydrateUser(res.access_token);
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [hydrateUser]
  );

  const signup = useCallback(async (payload: SignupPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      // Real backend does not return a token from /signup, and by default
      // (REQUIRE_EMAIL_VERIFICATION=true) will refuse to log the account in
      // until the emailed verification link is clicked. So we do NOT chain
      // into login() here — we just report the backend's own message back
      // to the caller and let the Signup page route to "check your email".
      const res = await authService.signup(payload);
      return res.message;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteAccount = useCallback(
    async (password: string) => {
      if (!accessToken) {
        throw new Error("Not authenticated");
      }
      setIsLoading(true);
      setError(null);
      try {
        const payload: DeleteAccountPayload = { password };
        await authService.deleteAccount(payload, accessToken);
        // Account is gone server-side — clear local session immediately.
        setUser(null);
        setAccessToken(null);
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [accessToken]
  );

  const logout = useCallback(async () => {
    // Real backend does have a /logout endpoint (confirmed against the backend
    // developer report — it bumps token_version server-side, invalidating this
    // token immediately, not just clearing it from the browser).
    const tokenToInvalidate = accessToken;
    // Clear local state first so the UI responds instantly regardless of the
    // network call's outcome — the user should never feel "stuck" on logout.
    setUser(null);
    setAccessToken(null);
    setError(null);

    if (tokenToInvalidate) {
      try {
        await authService.logout(tokenToInvalidate);
      } catch {
        // If this fails (token already expired, network down, etc.), it's not
        // actionable for the user — they're already logged out locally, and an
        // already-invalid token needs no further invalidation. Fail silently.
      }
    }
  }, [accessToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isAuthenticated: Boolean(user && accessToken),
      isLoading,
      error,
      signup,
      login,
      logout,
      deleteAccount,
      clearError,
    }),
    [user, accessToken, isLoading, error, signup, login, logout, deleteAccount, clearError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
