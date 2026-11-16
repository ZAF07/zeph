import type { HeldBack, HoldBackReason } from "@/lib/api-client";
import { toTimeFieldValue } from "@/lib/check-ins";
import { dateParts } from "@/lib/dates";

const minute = 60 * 1000;
const hour = 60 * minute;
const day = 24 * hour;

/** What the Schedule calls each reason a Check-in is held back. */
export const holdBackReasonLabels: Record<HoldBackReason, string> = {
  check_ins_off: "Check-ins off",
  paused: "Paused",
  quiet_hours: "Quiet Hours",
  no_telegram_connection: "No Telegram Connection",
  in_conversation: "In a Conversation",
  limit_skip_done_today: "Today’s message limit used up",
  no_kind_to_send: "No Kind to send",
};

/**
 * Writes a moment in the User's time, like "Tue 13:00".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The User's time zone; the browser's when unknown.
 * @returns The weekday and time.
 */
function weekdayAndTime(isoTimestamp: string, timeZone?: string): string {
  const part = dateParts(new Date(isoTimestamp), {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  });
  return `${part("weekday")} ${part("hour")}:${part("minute")}`;
}

/**
 * Writes a moment in the User's time, like "Tue 24 Nov 10:00".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The User's time zone; the browser's when unknown.
 * @returns The weekday, day, month and time.
 */
function dayAndTime(isoTimestamp: string, timeZone?: string): string {
  const part = dateParts(new Date(isoTimestamp), {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  });
  return `${part("weekday")} ${part("day")} ${part("month")} ${part("hour")}:${part("minute")}`;
}

/**
 * Writes a moment's time of day in the User's time, like "07:30".
 *
 * @param isoTimestamp - The moment, as the backend sends it.
 * @param timeZone - The User's time zone; the browser's when unknown.
 * @returns The hours and minutes.
 */
function timeOnly(isoTimestamp: string, timeZone?: string): string {
  const part = dateParts(new Date(isoTimestamp), {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  });
  return `${part("hour")}:${part("minute")}`;
}

/**
 * Says how long from now something is, like "in 40 min", "in 3 h" or "in 3 d".
 *
 * @param milliseconds - How long from now; more than zero.
 * @returns The words.
 */
function fromNowText(milliseconds: number): string {
  if (milliseconds < hour) {
    return `in ${Math.max(1, Math.round(milliseconds / minute))} min`;
  }
  if (milliseconds < 2 * day) {
    return `in ${Math.round(milliseconds / hour)} h`;
  }
  return `in ${Math.round(milliseconds / day)} d`;
}

/**
 * Writes a User's Due Time for the Schedule, like "in 3 h · Tue 13:00 their
 * time", or "due now" once it has come.
 *
 * @param nextDueAt - Their Due Time; null for none.
 * @param now - When the backend read the Schedule.
 * @param timeZone - The User's time zone; the browser's when unknown.
 * @returns The words.
 */
export function dueTimeText(
  nextDueAt: string | null,
  now: string,
  timeZone?: string,
): string {
  if (nextDueAt === null) {
    return "No Due Time";
  }
  const untilDue = Date.parse(nextDueAt) - Date.parse(now);
  if (untilDue <= 0) {
    return "due now";
  }
  return `${fromNowText(untilDue)} · ${weekdayAndTime(nextDueAt, timeZone)} their time`;
}

/**
 * Says why a Check-in is held back and until when, like "Quiet Hours, until
 * 07:30". A time within a day is shown alone; a later one with its day.
 *
 * @param heldBack - Why it is held back and until when.
 * @param now - When the backend read the Schedule.
 * @param timeZone - The User's time zone; the browser's when unknown.
 * @returns The words.
 */
export function heldBackText(
  heldBack: HeldBack,
  now: string,
  timeZone?: string,
): string {
  const reason = holdBackReasonLabels[heldBack.reason];
  if (heldBack.until === null) {
    return reason;
  }
  const isWithinADay = Date.parse(heldBack.until) - Date.parse(now) < day;
  const until = isWithinADay
    ? timeOnly(heldBack.until, timeZone)
    : dayAndTime(heldBack.until, timeZone);
  return `${reason}, until ${until}`;
}

/**
 * Writes Quiet Hours as a range, like "22:00–07:30".
 *
 * @param start - When they start, as the backend sends it, e.g. "22:00:00".
 * @param end - When they end, as the backend sends it.
 * @returns The range.
 */
export function quietHoursText(start: string, end: string): string {
  return `${toTimeFieldValue(start)}–${toTimeFieldValue(end)}`;
}

/**
 * Says whether a User's Check-ins are paused and until when, like "Paused
 * until Tue 24 Nov 10:00".
 *
 * @param paused - Whether they are paused right now.
 * @param pausedUntil - When the pause ends; null until resumed.
 * @param timeZone - The User's time zone; the browser's when unknown.
 * @returns The words.
 */
export function schedulePauseText(
  paused: boolean,
  pausedUntil: string | null,
  timeZone?: string,
): string {
  if (!paused) {
    return "Not paused";
  }
  if (pausedUntil === null) {
    return "Paused until resumed";
  }
  return `Paused until ${dayAndTime(pausedUntil, timeZone)}`;
}
