import { type ReactNode } from "react";

type PanelProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function Panel({ title, subtitle, action, children }: PanelProps) {
  return (
    <section className="panel min-w-0 w-full">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="panel-title">{title}</h3>
          {subtitle ? <p className="panel-subtitle">{subtitle}</p> : null}
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}
