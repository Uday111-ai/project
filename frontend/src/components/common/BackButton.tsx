import { useNavigate } from "react-router-dom";

interface BackButtonProps {
  fallback?: string;
  className?: string;
}

export function BackButton({ fallback = "/", className = "" }: BackButtonProps) {
  const navigate = useNavigate();

  function handleClick() {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate(fallback);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label="Go back"
      className={
        "inline-flex h-9 w-9 items-center justify-center rounded-full " +
        "bg-slate-100/80 text-slate-500 ring-1 ring-slate-200 " +
        "transition-colors hover:bg-slate-200 hover:text-slate-700 " +
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 " +
        className
      }
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-4 w-4"
      >
        <path d="M11 6 5 12l6 6" />
        <path d="M5 12h8a5 5 0 0 1 5 5v1" />
      </svg>
    </button>
  );
}