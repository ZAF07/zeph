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
