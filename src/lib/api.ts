// Real HTTP client — every call here goes to the actual FastAPI backend.
// Base URL comes from the environment (see .env: VITE_API_BASE_URL).
// This is Backend/DB Connection Checkpoint #1 from the authentication plan (Section 16).

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

if (!API_BASE_URL) {
  // Fail loudly in dev rather than silently calling a wrong/undefined URL.
  // eslint-disable-next-line no-console
  console.error(
    "VITE_API_BASE_URL is not set. Check your .env file — it must point at the real running backend " +
      "(e.g. http://localhost:8000)."
  );
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  token?: string | null;
}

/**
 * Makes a real network request to the backend. No mock branches, no fake data —
 * if the backend is not running at API_BASE_URL, this will throw a network error,
 * which is the correct, honest behavior.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    // Real network failure — backend unreachable, CORS blocked, DNS, etc.
    throw new ApiError(0, "Could not reach the server. Please check your connection.", networkErr);
  }

  let data: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const message = extractErrorMessage(data, response.status);
    throw new ApiError(response.status, message, data);
  }

  return data as T;
}

/**
 * Turns FastAPI/Pydantic-style error bodies into a single human-readable message.
 * Handles: {detail: "string"} and {detail: [{msg, loc}, ...]}.
 */
function extractErrorMessage(data: unknown, status: number): string {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: unknown }).msg) : ""))
        .filter(Boolean)
        .join(" ");
    }
  }
  switch (status) {
    case 401:
      return "Incorrect email or password.";
    case 409:
      return "That username or email is already registered.";
    case 400:
      return "This reset link is no longer valid. Please request a new one.";
    case 500:
      return "Something went wrong on our end. Please try again shortly.";
    default:
      return "Something went wrong. Please try again.";
  }
}
