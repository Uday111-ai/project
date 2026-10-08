import { useState, type FormEvent } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";

interface FieldErrors {
  email?: string;
  otp_code?: string;
}

export default function VerifyEmailOtp() {
  const navigate = useNavigate();
  const location = useLocation();
  const prefillEmail = (location.state as { email?: string } | null)?.email ?? "";

  const [email, setEmail] = useState(prefillEmail);
  const [otpCode, setOtpCode] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const errors: FieldErrors = {};
    if (!email.trim()) errors.email = "Email is required.";
    if (!otpCode) {
      errors.otp_code = "Code is required.";
    } else if (!/^\d{6}$/.test(otpCode)) {
      errors.otp_code = "Enter the 6-digit code.";
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    try {
      const res = await authService.verifyEmailOtp({
        email: email.trim(),
        otp_code: otpCode,
      });
      navigate("/login", { replace: true, state: { successMessage: res.message } });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setSubmitError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthLayout title="Verify your email" subtitle="Enter the 6-digit code we sent to your email.">
      <form onSubmit={handleSubmit} noValidate>
        <AuthFormError message={submitError} />

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

        <Input
          label="6-digit code"
          name="otp_code"
          type="text"
          inputMode="numeric"
          maxLength={6}
          autoComplete="one-time-code"
          value={otpCode}
          onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
          errorMessage={fieldErrors.otp_code}
          disabled={isLoading}
        />

        <Button type="submit" isLoading={isLoading}>
          Verify email
        </Button>

        <p className="mt-4 text-center text-sm text-slate-500">
          <Link to="/resend-verification" className="font-medium text-blue-600 hover:text-blue-800">
            Didn't get a code? Resend
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}