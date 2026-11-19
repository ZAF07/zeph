import { describe, expect, it } from "vitest";

import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInFrequencyText,
  greeting,
  homePauseEndText,
  lastCheckInText,
  lastTalkedText,
  quietHoursText,
} from "@/lib/home";
import { seedCopy } from "@/test/copy";

const singapore = "Asia/Singapore";
const copy = seedCopy();

function checkInWith(overrides: Partial<RecentCheckIn> = {}): RecentCheckIn {
  return {
    id: "c1",
    outcome: "sent",
    kind: "A casual hello",
    decided_at: "2026-11-10T10:00:00Z",
    status: "replied",
    skipped_for_daily_limit: false,
    ...overrides,
  };
}

describe("home wording", () => {
  it("greets the User for the time of day where they are", () => {
    expect(
      greeting(copy, "Maya", new Date("2026-11-11T01:00:00Z"), singapore),
    ).toBe("Good morning, Maya.");
    expect(
      greeting(copy, "Maya", new Date("2026-11-11T06:00:00Z"), singapore),
    ).toBe("Good afternoon, Maya.");
    expect(
      greeting(copy, "Maya", new Date("2026-11-11T12:00:00Z"), singapore),
    ).toBe("Good evening, Maya.");
    expect(
      greeting(copy, null, new Date("2026-11-11T12:00:00Z"), singapore),
    ).toBe("Good evening.");
  });

  it("says when the User last talked with Zeph", () => {
    const now = new Date("2026-11-11T12:00:00Z");

    expect(lastTalkedText(copy, "2026-11-11T11:48:00Z", now, singapore)).toBe(
      "You last talked with Zeph today.",
    );
    expect(lastTalkedText(copy, "2026-11-10T11:48:00Z", now, singapore)).toBe(
      "You last talked with Zeph yesterday.",
    );
    expect(lastTalkedText(copy, "2026-11-02T01:05:00Z", now, singapore)).toBe(
      "You last talked with Zeph on 2 Nov.",
    );
    expect(lastTalkedText(copy, null, now, singapore)).toBe(
      "You haven't talked with Zeph yet.",
    );
  });

  it("says how often Check-ins come, as the choice is named", () => {
    expect(checkInFrequencyText(copy, "few_times_a_week")).toBe(
      "A few times a week",
    );
    expect(checkInFrequencyText(copy, "weekly")).toBe("Weekly");
  });

  it("writes quiet hours as times of day", () => {
    expect(quietHoursText(copy, "23:00:00", "07:00:00")).toBe(
      "11:00 PM to 7:00 AM",
    );
    expect(quietHoursText(copy, "22:00:00", "07:30:00")).toBe(
      "10:00 PM to 7:30 AM",
    );
  });

  it("names the day of the last Check-in, and whether the User replied", () => {
    const now = new Date("2026-11-17T12:00:00Z");

    expect(lastCheckInText(copy, checkInWith(), now, singapore)).toBe(
      "Tuesday · you replied",
    );
    expect(
      lastCheckInText(
        copy,
        checkInWith({ status: "no_reply" }),
        now,
        singapore,
      ),
    ).toBe("Tuesday · no reply");
    expect(
      lastCheckInText(
        copy,
        checkInWith({
          outcome: "asked_about_fewer",
          kind: null,
          status: "sent",
        }),
        now,
        singapore,
      ),
    ).toBe("Tuesday");
  });

  it("says today, yesterday, a weekday up to a week back, then the date", () => {
    const now = new Date("2026-11-17T12:00:00Z");
    const sentAt = (decidedAt: string) =>
      lastCheckInText(
        copy,
        checkInWith({ decided_at: decidedAt, status: "sent" }),
        now,
        singapore,
      );

    expect(sentAt("2026-11-17T02:00:00Z")).toBe("Today");
    expect(sentAt("2026-11-16T02:00:00Z")).toBe("Yesterday");
    expect(sentAt("2026-11-12T02:00:00Z")).toBe("Thursday");
    expect(sentAt("2026-11-09T02:00:00Z")).toBe("9 Nov");
  });

  it("says there has been no Check-in yet", () => {
    expect(lastCheckInText(copy, null, new Date(), singapore)).toBe("None yet");
  });

  it("says when a pause on Check-ins ends", () => {
    expect(homePauseEndText(copy, "2026-11-18T03:00:00Z", singapore)).toBe(
      "until Wednesday, 18 November",
    );
    expect(homePauseEndText(copy, null, singapore)).toBe("until you resume");
  });

  it("words every line from an Admin's Copy, filling in the live values", () => {
    const now = new Date("2026-11-17T12:00:00Z");
    const adminCopy = {
      ...copy,
      "home.hero.greeting_evening": "Evening {name}, welcome back.",
      "home.hero.last_talked_on_day": "Your last chat was {day}.",
      "home.check_ins.frequency_weekly": "Once a week",
      "home.check_ins.quiet_hours": "Quiet from {start} until {end}",
      "home.check_ins.last_yesterday": "The day before",
      "home.check_ins.last_replied": "You answered ({day})",
      "home.check_ins.paused_until_day": "till {day}",
    };

    expect(greeting(adminCopy, "Maya", now, singapore)).toBe(
      "Evening Maya, welcome back.",
    );
    expect(
      lastTalkedText(adminCopy, "2026-11-02T01:05:00Z", now, singapore),
    ).toBe("Your last chat was 2 Nov.");
    expect(checkInFrequencyText(adminCopy, "weekly")).toBe("Once a week");
    expect(quietHoursText(adminCopy, "23:00:00", "07:00:00")).toBe(
      "Quiet from 11:00 PM until 7:00 AM",
    );
    expect(
      lastCheckInText(
        adminCopy,
        checkInWith({ decided_at: "2026-11-16T02:00:00Z" }),
        now,
        singapore,
      ),
    ).toBe("You answered (The day before)");
    expect(homePauseEndText(adminCopy, "2026-11-18T03:00:00Z", singapore)).toBe(
      "till Wednesday, 18 November",
    );
  });
});
