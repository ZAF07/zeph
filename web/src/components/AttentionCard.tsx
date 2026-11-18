import type { ReactNode } from "react";

/**
 * The orange-outlined card for an empty state that blocks everything else,
 * such as Home before Telegram is connected.
 *
 * @param props - `title` says what is wrong, `body` explains it, and
 *   `action` is the way forward (usually a primary `PillLink`).
 * @returns The card.
 */
export function AttentionCard({
  title,
  body,
  action,
}: {
  title: string;
  body: ReactNode;
  action: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 rounded-card border border-orange px-6 py-5">
      <div className="flex-[1_1_240px]">
        <div className="text-[17px] font-normal text-cream">{title}</div>
        <p className="mt-1 mb-0 text-[14px] text-soft">{body}</p>
      </div>
      {action}
    </div>
  );
}
