import { useState, useEffect, useRef, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Input } from "../components/common/Input";
import { PasswordInput } from "../components/auth/PasswordInput";
import { Button } from "../components/common/Button";
import { AuthFormError } from "../components/auth/AuthFormError";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";
import { authService } from "../services/authService";

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
  } else if (!/\d/.test(values.create_password)) {
    errors.create_password = "Password must include at least one digit.";
  } else if (!/[^A-Za-z0-9]/.test(values.create_password)) {
    errors.create_password = "Password must include at least one special character.";
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

  // Live GET /check-username, debounced 400ms behind typing so a normal user
  // typing one username stays well under the endpoint's 30/minute rate limit.
  const [usernameStatus, setUsernameStatus] = useState<{
    checking: boolean;
    available: boolean | null;
    suggestions: string[];
  }>({ checking: false, available: null, suggestions: [] });
  const usernameCheckId = useRef(0);

  useEffect(() => {
    const trimmed = values.username.trim();
    if (trimmed.length < 3) {
      // Nothing to invalidate — the render below only reads usernameStatus
      // once trimmed.length >= 3, so a stale value here is never shown.
      usernameCheckId.current++;
      return;
    }

    const thisCheckId = ++usernameCheckId.current;
    setUsernameStatus((prev) => ({ ...prev, checking: true }));

    const timer = setTimeout(async () => {
      try {
        const res = await authService.checkUsername(trimmed);
        if (usernameCheckId.current !== thisCheckId) return; // stale response, a newer check is in flight
        setUsernameStatus({
          checking: false,
          available: res.available,
          suggestions: res.suggestions ?? [],
        });
      } catch {
        if (usernameCheckId.current !== thisCheckId) return;
        // Non-blocking: if the check itself fails, don't stop the user from
        // submitting — the backend still validates uniqueness on /signup.
        setUsernameStatus({ checking: false, available: null, suggestions: [] });
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [values.username]);

  function handleChange(field: keyof typeof values, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  function applySuggestion(name: string) {
    setValues((prev) => ({ ...prev, username: name }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    clearError();

    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      // Real call: POST /signup on the real backend. It does NOT auto-login
      // (confirmed) and, with REQUIRE_EMAIL_VERIFICATION on by default, the
      // account can't log in yet anyway — so send the user to check their
      // inbox instead of straight to the dashboard.
      const message = await signup(values);
      navigate("/login", {
        replace: true,
        state: { successMessage: message },
      });
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
      // Other errors (network, 500) are already shown via the shared `error`
      // state from AuthContext / AuthFormError below.
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
        {!fieldErrors.username && values.username.trim().length >= 3 && (
          <div className="-mt-3 mb-4 text-xs">
            {usernameStatus.checking && <span className="text-slate-400">Checking availability…</span>}
            {!usernameStatus.checking && usernameStatus.available === true && (
              <span className="text-green-600">✓ Username is available.</span>
            )}
            {!usernameStatus.checking && usernameStatus.available === false && (
              <div className="text-amber-600">
                <span>That username is taken.</span>
                {usernameStatus.suggestions.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {usernameStatus.suggestions.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => applySuggestion(s)}
                        className="rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 font-medium text-amber-700 hover:bg-amber-100"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

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
        {!fieldErrors.create_password && (
          <p className="-mt-3 mb-4 text-xs text-slate-400">
            8+ characters, with at least one digit and one special character.
          </p>
        )}

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
