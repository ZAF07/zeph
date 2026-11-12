/**
 * Splits a moment into named date parts, like its weekday and month.
 *
 * @param moment - The moment.
 * @param options - Which parts to write and how.
 * @returns A function that gives one part's text, or "" if it has none.
 */
export function dateParts(
  moment: Date,
  options: Intl.DateTimeFormatOptions,
): (type: Intl.DateTimeFormatPartTypes) => string {
  const parts = new Intl.DateTimeFormat("en-GB", options).formatToParts(moment);
  return (type) => parts.find((entry) => entry.type === type)?.value ?? "";
}

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

/**
 * Writes the day something was added: "Today", "Yesterday" or like "2 Oct".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param now - The current moment.
 * @param timeZone - The time zone to count days in; the browser's by default.
 * @returns The day.
 */
export function formatAddedDay(
  isoTimestamp: string,
  now: Date,
  timeZone?: string,
): string {
  const calendarDay = new Intl.DateTimeFormat("en-CA", { timeZone });
  const added = calendarDay.format(new Date(isoTimestamp));
  if (added === calendarDay.format(now)) {
    return "Today";
  }
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  if (added === calendarDay.format(yesterday)) {
    return "Yesterday";
  }
  return formatShortDay(isoTimestamp, timeZone);
}
