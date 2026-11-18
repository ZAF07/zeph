import type { ReactNode } from "react";

/**
 * The row shown when a feature is switched off or paused, such as "Memory is
 * off" or "Check-ins are paused until 25 Nov", with the way to turn it back on.
 *
 * @param props - `title` says what is off, `body` what that means, and
 *   `action` is the optional way to turn it back on (usually a secondary
 *   button).
 * @returns The notice.
 */
export function PausedNotice({
  title,
  body,
  action,
}: {
  title: string;
  body: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-5 gap-y-2.5 rounded-tile border border-line px-[22px] py-[18px]">
      <div className="min-w-0 flex-[1_1_260px]">
        <div className="text-[15px] font-normal text-text">{title}</div>
        <div className="text-[13px] text-soft">{body}</div>
      </div>
      {action}
    </div>
  );
}
