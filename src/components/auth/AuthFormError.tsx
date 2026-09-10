interface AuthFormErrorProps {
  message: string | null;
}

// Renders only clean, human-readable messages (already converted from the real API
// error response in lib/api.ts). Never pass a raw error object or stack trace here.
export function AuthFormError({ message }: AuthFormErrorProps) {
  if (!message) return null;
  return (
    <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {message}
    </div>
  );
}
