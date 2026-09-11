import { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { AuthLayout } from "../components/auth/AuthLayout";
import { authService } from "../services/authService";
import { ApiError } from "../lib/api";

// Real call: POST /verify-email. The token comes from the URL query string
// (?token=...) that the emailed "verify your account" link points at
// (config.FRONTEND_URL + "/verify-email?token=..." on the backend, matching
// this route exactly). Fires automatically on mount — no form to submit.

type Status = "verifying" | "success" | "error";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [status, setStatus] = useState<Status>(token ? "verifying" : "error");
  const [message, setMessage] = useState<string>(
    token ? "" : "This verification link is missing its token."
  );
  const ranRef = useRef(false);

  useEffect(() => {
    if (!token || ranRef.current) return;
    ranRef.current = true; // guard against React StrictMode's double-invoke in dev

    authService
      .verifyEmail({ token })
      .then((res) => {
        setStatus("success");
        setMessage(res.message);
      })
      .catch((err) => {
        setStatus("error");
        // Backend returns 400 "Invalid or expired verification link" for a
        // used/expired/wrong token — surfaced as-is via ApiError.message.
        setMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      });
  }, [token]);

  return (
    <AuthLayout title="Verify your email">
      {status === "verifying" && <p className="text-sm text-slate-500">Verifying your email…</p>}

      {status === "success" && (
        <>
          <div className="mb-6 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
            {message}
          </div>
          <p className="text-center text-sm text-slate-500">
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-800">
              Continue to log in
            </Link>
          </p>
        </>
      )}

      {status === "error" && (
        <>
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {message}
          </div>
          <p className="text-center text-sm text-slate-500">
            <Link to="/resend-verification" className="font-medium text-blue-600 hover:text-blue-800">
              Request a new verification link
            </Link>
          </p>
        </>
      )}
    </AuthLayout>
  );
}
