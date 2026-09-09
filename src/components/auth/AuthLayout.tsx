import type { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="mb-1 text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="mb-6 text-sm text-slate-500">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}
