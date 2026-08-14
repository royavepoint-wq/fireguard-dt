import { type ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="mb-6 flex min-w-0 flex-col gap-4 border-b border-white/10 pb-4 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--fg-muted)]">FireGuard DT</p>
        <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">{title}</h1>
        <p className="mt-1 text-sm text-[var(--fg-muted)]">{description}</p>
      </div>
      {actions}
    </header>
  );
}
