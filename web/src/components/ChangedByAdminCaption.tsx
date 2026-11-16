import { formatShortDay } from "@/lib/dates";

/**
 * The small "Changed by an Admin · 15 Nov" line under a setting an Admin
 * last changed for the User, until the User changes it themselves.
 *
 * @param props - `changedAt` is when an Admin changed it, or undefined if
 *   they didn't; `timeZone` is the User's, to pick the day.
 * @returns The caption, or nothing.
 */
export function ChangedByAdminCaption({
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
    <span className="inline-flex items-center gap-1.5 text-caption text-yellow-deep">
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
        <path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z" />
      </svg>
      {`Changed by an Admin · ${formatShortDay(changedAt, timeZone)}`}
    </span>
  );
}
