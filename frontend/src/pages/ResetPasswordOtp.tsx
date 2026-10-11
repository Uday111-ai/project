import { useState, type FormEvent } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { PasswordInput } from "../components/auth/PasswordInput";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";

interface FieldErrors {
  email?: string;
  otp_code?: string;
  new_password?: string;
  confirm_password?: string;
}

interface Values {
  email: string;
  otp_code: string;
  new_password: string;
  confirm_password: string;
}

function validate(values: Values): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.email.trim()) {
    errors.email = "Email is required.";
  }

  if (!values.otp_code) {
    errors.otp_code = "Code is required.";
  } else if (!/^\d{6}$/.test(values.otp_code)) {
    errors.otp_code = "Enter the 6-digit code.";
  }

  if (!values.new_password) {
    errors.new_password = "Password is required.";
  } else if (values.new_password.length < 8) {
    errors.new_password = "Password must be at least 8 characters.";
  } else if (!/\d/.test(values.new_password)) {
    errors.new_password = "Password must include at least one digit.";
  } else if (!/[^A-Za-z0-9]/.test(values.new_password)) {
    errors.new_password = "Password must include at least one special character.";
  }

  if (!values.confirm_password) {
    errors.confirm_password = "Please confirm your password.";
  } else if (values.new_password !== values.confirm_password) {
    errors.confirm_password = "Passwords do not match.";
  }

  return errors;
}

export default function ResetPasswordOtp() {
  const navigate = useNavigate();
  const location = useLocation();
  const prefillEmail = (location.state as { email?: string } | null)?.email ?? "";

  const [values, setValues] = useState<Values>({
    email: prefillEmail,
    otp_code: "",
    new_password: "",
    confirm_password: "",
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function handleChange(field: keyof Values, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    try {
      const res = await authService.resetPasswordOtp({
        email: values.email.trim(),
        otp_code: values.otp_code,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
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
    <AuthLayout title="Enter your code" subtitle="We sent a 6-digit code to your email.">
      <form onSubmit={handleSubmit} noValidate>
        <AuthFormError message={submitError} />

        <Input
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          value={values.email}
          onChange={(e) => handleChange("email", e.target.value)}
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
          value={values.otp_code}
          onChange={(e) => handleChange("otp_code", e.target.value.replace(/\D/g, ""))}
          errorMessage={fieldErrors.otp_code}
          disabled={isLoading}
        />

        <PasswordInput
          label="New password"
          name="new_password"
          autoComplete="new-password"
          value={values.new_password}
          onChange={(e) => handleChange("new_password", e.target.value)}
          errorMessage={fieldErrors.new_password}
          disabled={isLoading}
        />
        {!fieldErrors.new_password && (
          <p className="-mt-3 mb-4 text-xs text-slate-400">
            8+ characters, with at least one digit and one special character.
          </p>
        )}

        <PasswordInput
          label="Confirm new password"
          name="confirm_password"
          autoComplete="new-password"
          value={values.confirm_password}
          onChange={(e) => handleChange("confirm_password", e.target.value)}
          errorMessage={fieldErrors.confirm_password}
          disabled={isLoading}
        />

        <Button type="submit" isLoading={isLoading}>
          Reset password
        </Button>

        <p className="mt-4 text-center text-sm text-slate-500">
          <Link to="/forgot-password" className="font-medium text-blue-600 hover:text-blue-800">
            Back to forgot password
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
