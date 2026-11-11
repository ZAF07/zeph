/**
 * Writes a day like "2 Oct 2026".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The time zone to show it in; the browser's by default.
 * @returns The day.
 */
export function formatDay(isoTimestamp: string, timeZone?: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone,
  }).format(new Date(isoTimestamp));
}

/**
 * Writes when something was saved, like "8 Nov, 14:20".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The time zone to show it in; the browser's by default.
 * @returns The day and time.
 */
export function formatSavedAt(isoTimestamp: string, timeZone?: string): string {
  const moment = new Date(isoTimestamp);
  const day = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    timeZone,
  }).format(moment);
  const time = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  }).format(moment);
  return `${day}, ${time}`;
}

/**
 * Writes a short day like "2 Oct", as memory sources show it.
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The time zone to show it in; the browser's by default.
 * @returns The day and month.
 */
export function formatShortDay(
  isoTimestamp: string,
  timeZone?: string,
): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    timeZone,
  }).format(new Date(isoTimestamp));
}

/**
 * Writes a day with its weekday like "Wed 11 Nov", as Conversation Summaries
 * show it.
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The time zone to show it in; the browser's by default.
 * @returns The weekday, day and month.
 */
export function formatWeekdayDay(
  isoTimestamp: string,
  timeZone?: string,
): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone,
  }).formatToParts(new Date(isoTimestamp));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((entry) => entry.type === type)?.value ?? "";
  return `${part("weekday")} ${part("day")} ${part("month")}`;
}
