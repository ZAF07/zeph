import type { CheckInFrequency, RecentCheckIn } from "@/lib/api-client";
import { formatQuietHour } from "@/lib/check-ins";
import { fillPlaceholders, readCopy, type Copy } from "@/lib/copy";
import {
  calendarDaysAgo,
  dateParts,
  formatLongDay,
  formatShortDay,
} from "@/lib/dates";

/**
 * Greets the User for the time of day where they are, like "Good evening,
 * Maya."
 *
 * @param copy - Home's Copy.
 * @param name - The User's name, if they gave one.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The greeting.
 */
export function greeting(
  copy: Copy,
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
  const key = `home.hero.greeting_${partOfDay}`;
  return name
    ? fillPlaceholders(readCopy(copy, key), { name })
    : readCopy(copy, `${key}_no_name`);
}

/**
 * Says when the User last talked with Zeph, like "You last talked with Zeph
 * yesterday."
 *
 * @param copy - Home's Copy.
 * @param lastConversationAt - When the last Conversation's newest message
 *   was sent; null if there has been none.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The sentence.
 */
export function lastTalkedText(
  copy: Copy,
  lastConversationAt: string | null,
  now: Date,
  timeZone?: string,
): string {
  if (lastConversationAt === null) {
    return readCopy(copy, "home.hero.last_talked_never");
  }
  const daysAgo = calendarDaysAgo(lastConversationAt, now, timeZone);
  if (daysAgo === 0) {
    return readCopy(copy, "home.hero.last_talked_today");
  }
  if (daysAgo === 1) {
    return readCopy(copy, "home.hero.last_talked_yesterday");
  }
  return fillPlaceholders(readCopy(copy, "home.hero.last_talked_on_day"), {
    day: formatShortDay(lastConversationAt, timeZone),
  });
}

/**
 * Names how often Check-ins may come, like "A few times a week".
 *
 * @param copy - Home's Copy.
 * @param frequency - The User's Check-in frequency.
 * @returns The name.
 */
export function checkInFrequencyText(
  copy: Copy,
  frequency: CheckInFrequency,
): string {
  return readCopy(copy, `home.check_ins.frequency_${frequency}`);
}

/**
 * Writes quiet hours, like "11:00 PM to 7:00 AM".
 *
 * @param copy - Home's Copy.
 * @param start - When quiet hours start, like "23:00:00".
 * @param end - When they end, like "07:00:00".
 * @returns The line.
 */
export function quietHoursText(copy: Copy, start: string, end: string): string {
  return fillPlaceholders(readCopy(copy, "home.check_ins.quiet_hours"), {
    start: formatQuietHour(start),
    end: formatQuietHour(end),
  });
}

/**
 * Says when a pause on Check-ins ends, like "until Thursday, 12 November".
 *
 * @param copy - Home's Copy.
 * @param pausedUntil - When the pause ends; null until the User resumes.
 * @param timeZone - The time zone to show the day in.
 * @returns The words after "Paused".
 */
export function homePauseEndText(
  copy: Copy,
  pausedUntil: string | null,
  timeZone?: string,
): string {
  if (pausedUntil === null) {
    return readCopy(copy, "home.check_ins.paused_until_resume");
  }
  return fillPlaceholders(readCopy(copy, "home.check_ins.paused_until_day"), {
    day: formatLongDay(pausedUntil, timeZone),
  });
}

/**
 * Names the day of the last Check-in sent and whether the User replied, like
 * "Tuesday · you replied". The day is "Today", "Yesterday", a weekday up to a
 * week back, then a date like "9 Nov". Never its Kind or message.
 *
 * @param copy - Home's Copy.
 * @param checkIn - The last Check-in sent, or null if none was.
 * @param now - The current moment.
 * @param timeZone - The User's time zone; the browser's by default.
 * @returns The line.
 */
export function lastCheckInText(
  copy: Copy,
  checkIn: RecentCheckIn | null,
  now: Date,
  timeZone?: string,
): string {
  if (checkIn === null) {
    return readCopy(copy, "home.check_ins.last_none");
  }
  const day = recentDayName(copy, checkIn.decided_at, now, timeZone);
  if (checkIn.status === "replied") {
    return fillPlaceholders(readCopy(copy, "home.check_ins.last_replied"), {
      day,
    });
  }
  if (checkIn.status === "no_reply") {
    return fillPlaceholders(readCopy(copy, "home.check_ins.last_no_reply"), {
      day,
    });
  }
  return day;
}

/**
 * Names a recent day: "Today", "Yesterday", its weekday up to a week back,
 * then a date like "9 Nov".
 *
 * @param copy - Home's Copy.
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param now - The current moment.
 * @param timeZone - The time zone to count days in.
 * @returns The day's name.
 */
function recentDayName(
  copy: Copy,
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
  if (daysAgo === 1) {
    return readCopy(copy, "home.check_ins.last_yesterday");
  }
  return readCopy(copy, "home.check_ins.last_today");
}
