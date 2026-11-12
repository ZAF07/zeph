import type { CheckInFrequency, CheckInStatus } from "@/lib/api-client";

/** The frequencies a User can pick, in the order they are shown. */
export const checkInFrequencyOptions: {
  value: CheckInFrequency;
  label: string;
}[] = [
  { value: "weekly", label: "Once a week" },
  { value: "few_times_a_week", label: "A few times a week" },
  { value: "most_days", label: "Most days" },
];

/** What each Check-in status is called, and its pill's colours. */
export const checkInStatusLabels: Record<
  CheckInStatus,
  { label: string; pill: string }
> = {
  sent: { label: "Sent", pill: "bg-code text-ink-body" },
  replied: { label: "Replied", pill: "bg-blue-tint text-blue-deep" },
  no_reply: { label: "No reply", pill: "bg-code text-ink-body" },
};

/**
 * Turns a backend time of day like "22:00:00" into a time field's "22:00".
 *
 * @param timeOfDay - The time as the backend sends it.
 * @returns The hours and minutes.
 */
export function toTimeFieldValue(timeOfDay: string): string {
  return timeOfDay.slice(0, 5);
}

/**
 * Splits a moment into named date parts, like its weekday and month.
 *
 * @param moment - The moment.
 * @param options - Which parts to write and how.
 * @returns A function that gives one part's text, or "" if it has none.
 */
function dateParts(
  moment: Date,
  options: Intl.DateTimeFormatOptions,
): (type: Intl.DateTimeFormatPartTypes) => string {
  const parts = new Intl.DateTimeFormat("en-GB", options).formatToParts(moment);
  return (type) => parts.find((entry) => entry.type === type)?.value ?? "";
}

/**
 * Says how long Check-ins are paused for, like "Paused until Thursday,
 * 12 November."
 *
 * @param pausedUntil - When the pause ends; null until the User resumes.
 * @param timeZone - The time zone to show the day in.
 * @returns The sentence.
 */
export function pausedText(
  pausedUntil: string | null,
  timeZone?: string,
): string {
  if (pausedUntil === null) {
    return "Paused until you resume.";
  }
  const part = dateParts(new Date(pausedUntil), {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone,
  });
  return `Paused until ${part("weekday")}, ${part("day")} ${part("month")}.`;
}

/**
 * Writes when a Check-in was sent, like "Mon 9 Nov · 6:42 pm".
 *
 * @param isoTimestamp - When it was sent, as the backend sends it.
 * @param timeZone - The time zone to show it in.
 * @returns The day and time.
 */
export function formatCheckInSentAt(
  isoTimestamp: string,
  timeZone?: string,
): string {
  const moment = new Date(isoTimestamp);
  const part = dateParts(moment, {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone,
  });
  const time = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone,
  })
    .format(moment)
    .replace(/\s/g, " ")
    .toLowerCase();
  return `${part("weekday")} ${part("day")} ${part("month")} · ${time}`;
}
