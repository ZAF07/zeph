import type {
  CheckInFrequency,
  CheckInStatus,
  RecentCheckIn,
} from "@/lib/api-client";
import { dateParts, formatLongDay, formatShortDay } from "@/lib/dates";

/** The frequencies a User can pick, in the order they are shown. */
export const checkInFrequencyOptions: {
  value: CheckInFrequency;
  label: string;
}[] = [
  { value: "weekly", label: "Weekly" },
  { value: "few_times_a_week", label: "A few times a week" },
  { value: "most_days", label: "Most days" },
  { value: "a_few_times_a_day", label: "A few times a day" },
];

/**
 * What each Check-in status is called, and whether its pill is the filled
 * one (only for a reply).
 */
export const checkInStatusLabels: Record<
  CheckInStatus,
  { label: string; isFilled: boolean }
> = {
  sent: { label: "Sent", isFilled: false },
  replied: { label: "Replied", isFilled: true },
  no_reply: { label: "No reply", isFilled: false },
  skipped: { label: "Skipped", isFilled: false },
};

/**
 * Names a recent Check-in for the User: its Kind, that they had reached the
 * day's message limit, or that Zeph gave them space or asked about fewer.
 * Never the Check-in model's reason for a skip.
 *
 * @param checkIn - The recent Check-in.
 * @returns The line to show.
 */
export function recentCheckInTitle(checkIn: RecentCheckIn): string {
  if (checkIn.skipped_for_daily_limit) {
    return "Skipped — you’d reached today’s message limit";
  }
  if (checkIn.outcome === "skipped") {
    return "Zeph gave you space";
  }
  if (checkIn.outcome === "asked_about_fewer") {
    return "Asked if you’d like fewer";
  }
  return checkIn.kind ?? "A check-in";
}

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
 * Writes a backend time of day like "23:00:00" as "11:00 PM", for the quiet
 * hours sentence.
 *
 * @param timeOfDay - The time as the backend sends it.
 * @returns The time on a 12-hour clock.
 */
export function formatQuietHour(timeOfDay: string): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  })
    .format(new Date(`1970-01-01T${toTimeFieldValue(timeOfDay)}:00Z`))
    .replace(/\s/g, " ");
}

/**
 * Says how long Check-ins are paused for, like "Check-ins are paused until
 * 25 Nov".
 *
 * @param pausedUntil - When the pause ends; null until the User resumes.
 * @param timeZone - The time zone to show the day in.
 * @returns The sentence.
 */
export function pausedText(
  pausedUntil: string | null,
  timeZone?: string,
): string {
  const until =
    pausedUntil === null ? "you resume" : formatShortDay(pausedUntil, timeZone);
  return `Check-ins are paused until ${until}`;
}

/**
 * Says when a pause on Check-ins ends, like "until Thursday, 12 November".
 *
 * @param pausedUntil - When the pause ends; null until the User resumes.
 * @param timeZone - The time zone to show the day in.
 * @returns The words after "Paused".
 */
export function pauseEndText(
  pausedUntil: string | null,
  timeZone?: string,
): string {
  if (pausedUntil === null) {
    return "until you resume";
  }
  return `until ${formatLongDay(pausedUntil, timeZone)}`;
}

/**
 * Writes the time of day of a moment, like "6:42 pm".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The time zone to show it in.
 * @returns The time.
 */
export function formatTimeOfDay(
  isoTimestamp: string,
  timeZone?: string,
): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone,
  })
    .format(new Date(isoTimestamp))
    .replace(/\s/g, " ")
    .toLowerCase();
}

/**
 * Writes the day of a Check-in, like "Saturday 7 Nov".
 *
 * @param isoTimestamp - When it was decided, as the backend sends it.
 * @param timeZone - The time zone to show it in.
 * @returns The day.
 */
export function formatCheckInDay(
  isoTimestamp: string,
  timeZone?: string,
): string {
  const part = dateParts(new Date(isoTimestamp), {
    weekday: "long",
    day: "numeric",
    month: "short",
    timeZone,
  });
  return `${part("weekday")} ${part("day")} ${part("month")}`;
}
