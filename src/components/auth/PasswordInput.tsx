import { useState, type InputHTMLAttributes } from "react";

interface PasswordInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  errorMessage?: string;
}

export function PasswordInput({ label, errorMessage, id, className = "", ...rest }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  const inputId = id ?? rest.name;

  return (
    <div className="mb-4">
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          type={visible ? "text" : "password"}
          aria-invalid={Boolean(errorMessage)}
          aria-describedby={errorMessage ? `${inputId}-error` : undefined}
          className={
            "w-full rounded-lg border px-3 py-2 pr-16 text-sm text-slate-800 outline-none transition " +
            "focus:ring-2 focus:ring-blue-400 " +
            (errorMessage ? "border-red-400" : "border-slate-300") +
            " " +
            className
          }
          {...rest}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-medium text-blue-600 hover:text-blue-800"
          tabIndex={-1}
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
      {errorMessage && (
        <p id={`${inputId}-error`} className="mt-1 text-xs text-red-600">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
