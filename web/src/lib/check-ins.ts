import type {
  CheckInFrequency,
  CheckInStatus,
  RecentCheckIn,
} from "@/lib/api-client";
import { fillCopy, readCopy, type Copy } from "@/lib/copy";
import { dateParts, formatShortDay } from "@/lib/dates";

/**
 * The frequencies a User can pick, in the order they are shown, with the
 * names admin pages use. Website pages name them from Copy with
 * `checkInFrequencyChoices`.
 */
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
 * The frequencies a User can pick, in the order they are shown, named with
 * the words onboarding gives them: their one home in Copy.
 *
 * @param copy - The page's Copy, with onboarding's frequency names.
 * @returns Each frequency with its name.
 */
export function checkInFrequencyChoices(
  copy: Copy,
): { value: CheckInFrequency; label: string }[] {
  return checkInFrequencyOptions.map((option) => ({
    value: option.value,
    label: readCopy(copy, `onboarding.check_ins.frequency_${option.value}`),
  }));
}

/**
 * Names a Check-in's status on the User's recent Check-ins, like "No reply".
 *
 * @param copy - The Check-ins page's Copy.
 * @param status - The Check-in's status.
 * @returns The status's name.
 */
export function checkInStatusText(copy: Copy, status: CheckInStatus): string {
  return readCopy(copy, `check_ins.recent.${status}`);
}

/**
 * Names a recent Check-in for the User: its Kind, that they had reached the
 * day's message limit, or that Zeph gave them space or asked about fewer.
 * Never the Check-in model's reason for a skip.
 *
 * @param copy - The Check-ins page's Copy.
 * @param checkIn - The recent Check-in.
 * @returns The line to show.
 */
export function recentCheckInTitle(copy: Copy, checkIn: RecentCheckIn): string {
  if (checkIn.skipped_for_daily_limit) {
    return readCopy(copy, "check_ins.recent.daily_limit");
  }
  if (checkIn.outcome === "skipped") {
    return readCopy(copy, "check_ins.recent.gave_space");
  }
  if (checkIn.outcome === "asked_about_fewer") {
    return readCopy(copy, "check_ins.recent.asked_about_fewer");
  }
  return checkIn.kind ?? readCopy(copy, "check_ins.recent.no_kind");
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
 * @param copy - The Check-ins page's Copy.
 * @param pausedUntil - When the pause ends; null until the User resumes.
 * @param timeZone - The time zone to show the day in.
 * @returns The sentence.
 */
export function pausedText(
  copy: Copy,
  pausedUntil: string | null,
  timeZone?: string,
): string {
  if (pausedUntil === null) {
    return readCopy(copy, "check_ins.paused.title_until_resume");
  }
  return fillCopy(copy, "check_ins.paused.title_until_day", {
    day: formatShortDay(pausedUntil, timeZone),
  });
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
