import { useState, type FormEvent } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { PasswordInput } from "../components/auth/PasswordInput";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { useAuth } from "../context/AuthContext";

// Login is EMAIL-ONLY — confirmed permanently with the backend team. No username field.

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { successMessage?: string } };
  const { login, isLoading, error, clearError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    clearError();

    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = "Email is required.";
    if (!password) errors.password = "Password is required.";
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      // Real call: POST /login on the real backend.
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch {
      // Generic 401 message is already surfaced via AuthContext's `error` state —
      // intentionally not distinguishing "wrong password" from "unknown email".
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

        <Input
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          errorMessage={fieldErrors.email}
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
