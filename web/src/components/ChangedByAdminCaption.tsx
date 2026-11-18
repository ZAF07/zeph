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
    <span className="text-[12px] text-soft">
      {`Changed by an Admin · ${formatShortDay(changedAt, timeZone)}`}
    </span>
  );
}
