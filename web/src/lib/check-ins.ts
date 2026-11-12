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
  const day = new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone,
  }).formatToParts(new Date(pausedUntil));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    day.find((entry) => entry.type === type)?.value ?? "";
  return `Paused until ${part("weekday")}, ${part("day")} ${part("month")}.`;
}

/**
 * Writes when a Check-in was sent, like "Sun 9 Nov · 6:42 pm".
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
  const parts = new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone,
  }).formatToParts(moment);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((entry) => entry.type === type)?.value ?? "";
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
