import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  errorMessage?: string;
}

export function Input({ label, errorMessage, id, className = "", ...rest }: InputProps) {
  const inputId = id ?? rest.name;
  return (
    <div className="mb-4">
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={Boolean(errorMessage)}
        aria-describedby={errorMessage ? `${inputId}-error` : undefined}
        className={
          "w-full rounded-lg border px-3 py-2 text-sm text-slate-800 outline-none transition " +
          "focus:ring-2 focus:ring-blue-400 " +
          (errorMessage ? "border-red-400" : "border-slate-300") +
          " " +
          className
        }
        {...rest}
      />
      {errorMessage && (
        <p id={`${inputId}-error`} className="mt-1 text-xs text-red-600">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
