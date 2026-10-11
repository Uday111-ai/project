import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { PasswordInput } from "../components/auth/PasswordInput";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";

// Real call: POST /reset-password. The token comes from the URL query string
// (?token=...) that the emailed reset link points at — the user never types it.
// Password rule mirrors the backend's real validator (app/schemas/user.py):
// 8+ characters, at least one digit, at least one special character.

interface FieldErrors {
  new_password?: string;
  confirm_password?: string;
}

function validate(values: { new_password: string; confirm_password: string }): FieldErrors {
  const errors: FieldErrors = {};

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

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [values, setValues] = useState({ new_password: "", confirm_password: "" });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function handleChange(field: keyof typeof values, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!token) {
      setSubmitError("This reset link is missing its token. Please request a new one.");
      return;
    }

    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    try {
      const res = await authService.resetPassword({
        token,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      });
      navigate("/login", { replace: true, state: { successMessage: res.message } });
    } catch (err) {
      // Backend returns 400 "Invalid or expired reset token" for a used/expired/
      // wrong token — surfaced as-is via ApiError.message.
      const msg = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setSubmitError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  if (!token) {
    return (
      <AuthLayout title="Reset your password" subtitle="This link looks incomplete.">
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          This reset link is missing its token. Please request a new one.
        </div>
        <p className="text-center text-sm text-slate-500">
          <Link to="/forgot-password" className="font-medium text-blue-600 hover:text-blue-800">
            Request a new reset link
          </Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Reset your password" subtitle="Choose a new password for your account.">
      <form onSubmit={handleSubmit} noValidate>
        <AuthFormError message={submitError} />

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
      </form>
    </AuthLayout>
  );
}
