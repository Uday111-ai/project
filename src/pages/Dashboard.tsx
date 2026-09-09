import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-2 text-sm text-slate-500">
        Real session data pulled from <code className="rounded bg-slate-100 px-1">GET /me</code>:
      </p>
      <pre className="mt-4 rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
        {JSON.stringify(user, null, 2)}
      </pre>
      <button
        onClick={logout}
        className="mt-6 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Log out
      </button>
    </div>
  );
}
