import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { PasswordInput } from "../components/auth/PasswordInput";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";

// Fields are FINAL per the confirmed plan: Username, Email, Create Password, Confirm Password.
// No Name field — confirmed with the backend team, do not add one.

interface FieldErrors {
  username?: string;
  email?: string;
  create_password?: string;
  confirm_password?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(values: {
  username: string;
  email: string;
  create_password: string;
  confirm_password: string;
}): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.username.trim()) {
    errors.username = "Username is required.";
  } else if (values.username.trim().length < 3) {
    errors.username = "Username must be at least 3 characters.";
  }

  if (!values.email.trim()) {
    errors.email = "Email is required.";
  } else if (!EMAIL_REGEX.test(values.email.trim())) {
    errors.email = "Enter a valid email address.";
  }

  if (!values.create_password) {
    errors.create_password = "Password is required.";
  } else if (values.create_password.length < 8) {
    errors.create_password = "Password must be at least 8 characters.";
  }

  if (!values.confirm_password) {
    errors.confirm_password = "Please confirm your password.";
  } else if (values.create_password !== values.confirm_password) {
    errors.confirm_password = "Passwords do not match.";
  }

  return errors;
}

export default function Signup() {
  const navigate = useNavigate();
  const { signup, isLoading, error, clearError } = useAuth();

  const [values, setValues] = useState({
    username: "",
    email: "",
    create_password: "",
    confirm_password: "",
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  function handleChange(field: keyof typeof values, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    clearError();

    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      // Real call: POST /signup on the real backend, then real POST /login to
      // establish a session (backend does not auto-login on signup — confirmed).
      await signup(values);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Backend currently returns a single generic conflict message — it does not
        // (yet) say which field conflicted. Surface it on both fields until the
        // backend teammate confirms a field-specific detail (Section 14, item 1).
        setFieldErrors((prev) => ({
          ...prev,
          username: "This username or email is already registered.",
        }));
      }
      // Other errors (401 from the follow-up login, network, 500) are already
      // shown via the shared `error` state from AuthContext / AuthFormError below.
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Start building your interview prep profile.">
      <form onSubmit={handleSubmit} noValidate>
        <AuthFormError message={error} />

        <Input
          label="Username"
          name="username"
          autoComplete="username"
          value={values.username}
          onChange={(e) => handleChange("username", e.target.value)}
          errorMessage={fieldErrors.username}
          disabled={isLoading}
        />

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

        <PasswordInput
          label="Create Password"
          name="create_password"
          autoComplete="new-password"
          value={values.create_password}
          onChange={(e) => handleChange("create_password", e.target.value)}
          errorMessage={fieldErrors.create_password}
          disabled={isLoading}
        />

        <PasswordInput
          label="Confirm Password"
          name="confirm_password"
          autoComplete="new-password"
          value={values.confirm_password}
          onChange={(e) => handleChange("confirm_password", e.target.value)}
          errorMessage={fieldErrors.confirm_password}
          disabled={isLoading}
        />

        <Button type="submit" isLoading={isLoading} className="mt-2">
          Create account
        </Button>

        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-800">
            Log in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
