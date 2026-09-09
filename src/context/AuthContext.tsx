import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from "react";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";
import type { CurrentUser, SignupPayload } from "../types/auth";

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
  signup: (payload: SignupPayload) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
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
    async (email: string, password: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await authService.login({ email, password });
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

  const signup = useCallback(
    async (payload: SignupPayload) => {
      setIsLoading(true);
      setError(null);
      try {
        // Real backend does not return a token from /signup (confirmed — Section 1/4).
        // So we call the real /signup endpoint, then immediately call the real /login
        // endpoint with the same credentials to establish a session.
        await authService.signup(payload);
        await login(payload.email, payload.create_password);
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [login]
  );

  const logout = useCallback(() => {
    // No backend /logout endpoint exists (confirmed — Section 9). JWTs are stateless,
    // so logout is purely a client-side token discard.
    setUser(null);
    setAccessToken(null);
    setError(null);
  }, []);

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
      clearError,
    }),
    [user, accessToken, isLoading, error, signup, login, logout, clearError]
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
