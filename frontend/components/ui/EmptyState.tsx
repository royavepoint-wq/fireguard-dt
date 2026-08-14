type EmptyStateProps = {
  title: string;
  description: string;
  bullets?: string[];
};

export function EmptyState({ title, description, bullets = [] }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <p className="mt-2 max-w-2xl text-sm text-[var(--fg-muted)]">{description}</p>
      {bullets.length > 0 ? (
        <ul className="mt-5 flex flex-wrap items-center justify-center gap-2">
          {bullets.map((item) => (
            <li key={item} className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200">
              {item}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
