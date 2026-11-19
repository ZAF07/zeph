import { fillPlaceholders } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";

/**
 * The small "Changed by an Admin · 15 Nov" line under a setting an Admin
 * last changed for the User, until the User changes it themselves.
 *
 * @param props - `changedAt` is when an Admin changed it, or undefined if
 *   they didn't; `timeZone` is the User's, to pick the day; `text` is the
 *   line's wording from Copy, with a `{day}` placeholder.
 * @returns The caption, or nothing.
 */
export function ChangedByAdminCaption({
  changedAt,
  timeZone,
  text,
}: {
  changedAt: string | undefined;
  timeZone?: string;
  text: string;
}) {
  if (!changedAt) {
    return null;
  }
  return (
    <span className="text-[12px] text-soft">
      {fillPlaceholders(text, { day: formatShortDay(changedAt, timeZone) })}
    </span>
  );
}
