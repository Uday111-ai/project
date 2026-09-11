import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";

// Real call: POST /forgot-password. The backend always returns the same generic
// message regardless of whether the account exists (prevents email enumeration),
// so this page never tries to distinguish "sent" from "no such account".

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!email.trim()) {
      setFieldError("Email is required.");
      return;
    }
    setFieldError(undefined);
    setIsLoading(true);

    try {
      const res = await authService.forgotPassword({ email: email.trim() });
      setMessage(res.message);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setSubmitError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  if (message) {
    return (
      <AuthLayout title="Check your email" subtitle="One more step to get back into your account.">
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
          {message}
        </div>
        <p className="text-center text-sm text-slate-500">
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-800">
            Back to log in
          </Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Forgot your password?"
      subtitle="Enter the email on your account and we'll send you a reset link."
    >
      <form onSubmit={handleSubmit} noValidate>
        <AuthFormError message={submitError} />

        <Input
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          errorMessage={fieldError}
          disabled={isLoading}
        />

        <Button type="submit" isLoading={isLoading}>
          Send reset link
        </Button>

        <p className="mt-4 text-center text-sm text-slate-500">
          Remembered it?{" "}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-800">
            Log in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
