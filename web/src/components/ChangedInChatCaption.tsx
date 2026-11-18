import { formatShortDay } from "@/lib/dates";

/**
 * The small "Changed in chat · 3 Nov" line under a setting the User
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
    <span className="text-[12px] text-soft">
      {`Changed in chat · ${formatShortDay(changedAt, timeZone)}`}
    </span>
  );
}
