import type {
  CheckInFrequency,
  CheckInStatus,
  RecentCheckIn,
} from "@/lib/api-client";
import {
  checkInFrequencyOptions,
  formatCheckInDay,
  formatTimeOfDay,
  recentCheckInTitle,
} from "@/lib/check-ins";
import { formatAddedDay } from "@/lib/dates";

const replyLabels: Record<CheckInStatus, string | null> = {
  replied: "you replied",
  no_reply: "no reply",
  sent: null,
  skipped: null,
};

/**
 * Greets the User for the time of day where they are, like "Good evening,
 * Maya."
 *
 * @param name - The User's name, if they gave one.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The greeting.
 */
export function greeting(
  name: string | null,
  now: Date,
  timeZone?: string,
): string {
  const hour = Number(
    new Intl.DateTimeFormat("en-GB", {
      hour: "numeric",
      hourCycle: "h23",
      timeZone,
    }).format(now),
  );
  const partOfDay = hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening";
  return name ? `Good ${partOfDay}, ${name}.` : `Good ${partOfDay}.`;
}

/**
 * Writes today's date where the User is, like "Wednesday, 11 November".
 *
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The date.
 */
export function todayHeading(now: Date, timeZone?: string): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone,
  }).formatToParts(now);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((entry) => entry.type === type)?.value ?? "";
  return `${part("weekday")}, ${part("day")} ${part("month")}`;
}

/**
 * Says when the User's last Conversation was, like "Last Conversation today
 * at 7:48 pm."
 *
 * @param lastConversationAt - When its newest message was sent; null if
 *   there has been none.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The sentence.
 */
export function lastConversationText(
  lastConversationAt: string | null,
  now: Date,
  timeZone?: string,
): string {
  if (lastConversationAt === null) {
    return "No Conversations yet. Say hello in Telegram.";
  }
  const day = formatAddedDay(lastConversationAt, now, timeZone);
  const when =
    day === "Today" || day === "Yesterday" ? day.toLowerCase() : `on ${day}`;
  return `Last Conversation ${when} at ${formatTimeOfDay(lastConversationAt, timeZone)}.`;
}

/**
 * Says how often Check-ins may come, like "A few times a week, at most".
 *
 * @param frequency - The User's Check-in frequency.
 * @returns The line.
 */
export function checkInFrequencyText(frequency: CheckInFrequency): string {
  const option = checkInFrequencyOptions.find(
    (entry) => entry.value === frequency,
  );
  return `${option?.label ?? "Now and then"}, at most`;
}

/**
 * Writes quiet hours, like "Never between 10:00 pm and 7:30 am".
 *
 * @param start - When quiet hours start, like "22:00:00".
 * @param end - When they end, like "07:30:00".
 * @returns The line.
 */
export function quietHoursText(start: string, end: string): string {
  return `Never between ${formatLocalTime(start)} and ${formatLocalTime(end)}`;
}

/**
 * Describes the last Check-in sent, like "Last Check-in: a casual hello,
 * Mon 9 Nov · you replied". Never its message.
 *
 * @param checkIn - The last Check-in sent, or null if none was.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The line.
 */
export function lastCheckInText(
  checkIn: RecentCheckIn | null,
  timeZone?: string,
): string {
  if (checkIn === null) {
    return "No Check-ins sent yet.";
  }
  const title = recentCheckInTitle(checkIn);
  const what = title.charAt(0).toLowerCase() + title.slice(1);
  const day = formatCheckInDay(checkIn.decided_at, timeZone);
  const reply = replyLabels[checkIn.status];
  return `Last Check-in: ${what}, ${day}${reply ? ` · ${reply}` : ""}`;
}

/**
 * Writes a time of day the backend sends, like "22:00:00", as "10:00 pm".
 *
 * @param timeOfDay - The time as the backend sends it.
 * @returns The time.
 */
function formatLocalTime(timeOfDay: string): string {
  const [hours, minutes] = timeOfDay.split(":").map(Number);
  const moment = new Date(Date.UTC(2000, 0, 1, hours, minutes));
  return formatTimeOfDay(moment.toISOString(), "UTC");
}
