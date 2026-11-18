import type { ReactNode } from "react";

/**
 * The dashed box shown when there is nothing yet: one plain sentence and the
 * next step if there is one.
 *
 * @param props - `title` names what is missing, `body` explains it, and
 *   `action` is the optional next step (usually a `PillLink`).
 * @returns The empty state.
 */
export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-2 rounded-card border border-dashed border-line-strong px-7 py-[26px]">
      <div className="text-[17px] font-normal text-cream">{title}</div>
      <p className="m-0 max-w-[460px] text-[14px] text-soft">{body}</p>
      {action}
    </div>
  );
}
