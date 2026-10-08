import { useState, type FormEvent } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { PasswordInput } from "../components/auth/PasswordInput";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { useAuth } from "../context/AuthContext";

// Login accepts EITHER an email or a username in one field — the backend's real
// LoginRequest field is `identifier` (see app/schemas/user.py), not `email`.

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { successMessage?: string } };
  const { login, isLoading, error, clearError } = useAuth();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ identifier?: string; password?: string }>({});

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    clearError();

    const errors: { identifier?: string; password?: string } = {};
    if (!identifier.trim()) errors.identifier = "Email or username is required.";
    if (!password) errors.password = "Password is required.";
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      // Real call: POST /login on the real backend. Can reject with 401 (bad
      // credentials), 403 (email not verified yet), or 423 (account locked) —
      // AuthContext surfaces the backend's own message for each via `error`.
      await login(identifier, password);
      navigate("/dashboard", { replace: true });
    } catch {
      // Message is already surfaced via AuthContext's `error` state below.
    }
  }

  return (
    <AuthLayout title="Log in" subtitle="Welcome back — pick up where you left off.">
      {location.state?.successMessage && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
          {location.state.successMessage}
        </div>
      )}
      <form onSubmit={handleSubmit} noValidate>
        <AuthFormError message={error} />
        {error?.toLowerCase().includes("verify") && (
          <p className="-mt-2 mb-4 text-xs text-slate-500">
            <Link to="/resend-verification" className="font-medium text-blue-600 hover:text-blue-800">
              Resend the verification email
            </Link>
          </p>
        )}

        <Input
          label="Email or username"
          name="identifier"
          type="text"
          autoComplete="username"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          errorMessage={fieldErrors.identifier}
          disabled={isLoading}
        />

        <PasswordInput
          label="Password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          errorMessage={fieldErrors.password}
          disabled={isLoading}
        />

        <div className="mb-4 text-right">
          <Link to="/forgot-password" className="text-xs font-medium text-blue-600 hover:text-blue-800">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" isLoading={isLoading}>
          Log in
        </Button>

        <p className="mt-4 text-center text-sm text-slate-500">
          Don't have an account?{" "}
          <Link to="/signup" className="font-medium text-blue-600 hover:text-blue-800">
            Sign up
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
