import { formatShortDay } from "@/lib/dates";

/**
 * The small blue "Changed in chat · 3 Nov" line under a setting the User
 * last changed by telling Zeph in chat.
 *
 * @param props - `changedAt` is when it was changed in chat, or undefined
 *   if it wasn't; `timeZone` is the User's, to pick the day.
 * @returns The caption, or nothing.
 */
export function ChangedInChatCaption({
  changedAt,
  timeZone,
}: {
  changedAt: string | undefined;
  timeZone?: string;
}) {
  if (!changedAt) {
    return null;
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-caption text-blue">
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" />
      </svg>
      {`Changed in chat · ${formatShortDay(changedAt, timeZone)}`}
    </span>
  );
}
