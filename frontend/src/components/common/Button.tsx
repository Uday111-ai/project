import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

export function Button({ isLoading, disabled, children, className = "", ...rest }: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={
        "w-full rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition " +
        "hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 " +
        "disabled:cursor-not-allowed disabled:bg-blue-300 " +
        className
      }
      {...rest}
    >
      {isLoading ? "Please wait…" : children}
    </button>
  );
}
