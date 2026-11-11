/**
 * The heading of an admin page: an "Admin" eyebrow, the title and a lead.
 *
 * @param props - `title` names the page; `lead` says what it is for.
 * @returns The header.
 */
export function AdminPageHeader({
  title,
  lead,
}: {
  title: string;
  lead: string;
}) {
  return (
    <header className="flex flex-col gap-2">
      <p className="m-0 font-mono text-caption font-semibold uppercase tracking-[0.06em] text-ink-muted">
        Admin
      </p>
      <h1 className="m-0 text-h1 font-normal">{title}</h1>
      <p className="m-0 max-w-[40em] text-body text-ink-soft">{lead}</p>
    </header>
  );
}
