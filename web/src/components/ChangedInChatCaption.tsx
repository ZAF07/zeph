import { fillPlaceholders } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";

/**
 * The small "Changed in chat · 3 Nov" line under a setting the User
 * last changed by telling Zeph in chat.
 *
 * @param props - `changedAt` is when it was changed in chat, or undefined
 *   if it wasn't; `timeZone` is the User's, to pick the day; `text` is the
 *   line's wording from Copy, with a `{day}` placeholder.
 * @returns The caption, or nothing.
 */
export function ChangedInChatCaption({
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
