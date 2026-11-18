import type {
  CheckInFrequency,
  CheckInStatus,
  RecentCheckIn,
} from "@/lib/api-client";
import { checkInFrequencyOptions, formatQuietHour } from "@/lib/check-ins";
import {
  calendarDaysAgo,
  dateParts,
  formatAddedDay,
  formatShortDay,
} from "@/lib/dates";

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
 * Says when the User last talked with Zeph, like "You last talked with Zeph
 * yesterday."
 *
 * @param lastConversationAt - When the last Conversation's newest message
 *   was sent; null if there has been none.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The sentence.
 */
export function lastTalkedText(
  lastConversationAt: string | null,
  now: Date,
  timeZone?: string,
): string {
  if (lastConversationAt === null) {
    return "You haven't talked with Zeph yet.";
  }
  const day = formatAddedDay(lastConversationAt, now, timeZone);
  const when =
    day === "Today" || day === "Yesterday" ? day.toLowerCase() : `on ${day}`;
  return `You last talked with Zeph ${when}.`;
}

/**
 * Names how often Check-ins may come, as the choice is called, like "A few
 * times a week".
 *
 * @param frequency - The User's Check-in frequency.
 * @returns The name.
 */
export function checkInFrequencyText(frequency: CheckInFrequency): string {
  const option = checkInFrequencyOptions.find(
    (entry) => entry.value === frequency,
  );
  return option?.label ?? "Now and then";
}

/**
 * Writes quiet hours, like "11:00 PM to 7:00 AM".
 *
 * @param start - When quiet hours start, like "23:00:00".
 * @param end - When they end, like "07:00:00".
 * @returns The line.
 */
export function quietHoursText(start: string, end: string): string {
  return `${formatQuietHour(start)} to ${formatQuietHour(end)}`;
}

/**
 * Names the day of the last Check-in sent and whether the User replied, like
 * "Tuesday · you replied". The day is "Today", "Yesterday", a weekday up to a
 * week back, then a date like "9 Nov". Never its Kind or message.
 *
 * @param checkIn - The last Check-in sent, or null if none was.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The line.
 */
export function lastCheckInText(
  checkIn: RecentCheckIn | null,
  now: Date,
  timeZone?: string,
): string {
  if (checkIn === null) {
    return "None yet";
  }
  const day = recentDayName(checkIn.decided_at, now, timeZone);
  const reply = replyLabels[checkIn.status];
  return reply ? `${day} · ${reply}` : day;
}

/**
 * Names a recent day: "Today", "Yesterday", its weekday up to a week back,
 * then a date like "9 Nov".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param now - The current moment.
 * @param timeZone - The time zone to count days in.
 * @returns The day's name.
 */
function recentDayName(
  isoTimestamp: string,
  now: Date,
  timeZone?: string,
): string {
  const daysAgo = calendarDaysAgo(isoTimestamp, now, timeZone);
  if (daysAgo > 7) {
    return formatShortDay(isoTimestamp, timeZone);
  }
  if (daysAgo > 1) {
    return dateParts(new Date(isoTimestamp), { weekday: "long", timeZone })(
      "weekday",
    );
  }
  return formatAddedDay(isoTimestamp, now, timeZone);
}
