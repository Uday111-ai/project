import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout, deleteAccount } = useAuth();

  const [confirming, setConfirming] = useState(false);
  const [password, setPassword] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleDelete(e: FormEvent) {
    e.preventDefault();
    setDeleteError(null);

    if (!password) {
      setDeleteError("Enter your current password to confirm.");
      return;
    }

    setIsDeleting(true);
    try {
      // Real call: POST /delete-account. Requires the current password as
      // confirmation and permanently deletes the account server-side.
      await deleteAccount(password);
      navigate("/signup", { replace: true, state: { successMessage: "Your account has been deleted." } });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setDeleteError(msg);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-2 text-sm text-slate-500">
        Real session data pulled from <code className="rounded bg-slate-100 px-1">GET /me</code>:
      </p>
      <pre className="mt-4 rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
        {JSON.stringify(user, null, 2)}
      </pre>

      {user && !user.email_verified && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
          Your email isn't verified yet.
        </div>
      )}

      <button
        onClick={logout}
        className="mt-6 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Log out
      </button>

      <div className="mt-10 border-t border-slate-200 pt-6">
        <h2 className="text-sm font-semibold text-slate-900">Danger zone</h2>
        <p className="mt-1 text-sm text-slate-500">
          Deleting your account is permanent and cannot be undone.
        </p>

        {!confirming ? (
          <button
            onClick={() => setConfirming(true)}
            className="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
          >
            Delete account
          </button>
        ) : (
          <form onSubmit={handleDelete} className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
            {deleteError && <p className="mb-3 text-sm text-red-700">{deleteError}</p>}
            <label htmlFor="delete-password" className="mb-1 block text-sm font-medium text-slate-700">
              Confirm with your current password
            </label>
            <input
              id="delete-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isDeleting}
              className="mb-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-red-400"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isDeleting}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
              >
                {isDeleting ? "Deleting…" : "Permanently delete"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setConfirming(false);
                  setPassword("");
                  setDeleteError(null);
                }}
                disabled={isDeleting}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
