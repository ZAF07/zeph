import { describe, expect, it } from "vitest";

import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInFrequencyText,
  greeting,
  lastCheckInText,
  lastTalkedText,
  quietHoursText,
} from "@/lib/home";

const singapore = "Asia/Singapore";

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
    expect(greeting("Maya", new Date("2026-11-11T01:00:00Z"), singapore)).toBe(
      "Good morning, Maya.",
    );
    expect(greeting("Maya", new Date("2026-11-11T06:00:00Z"), singapore)).toBe(
      "Good afternoon, Maya.",
    );
    expect(greeting("Maya", new Date("2026-11-11T12:00:00Z"), singapore)).toBe(
      "Good evening, Maya.",
    );
    expect(greeting(null, new Date("2026-11-11T12:00:00Z"), singapore)).toBe(
      "Good evening.",
    );
  });

  it("says when the User last talked with Zeph", () => {
    const now = new Date("2026-11-11T12:00:00Z");

    expect(lastTalkedText("2026-11-11T11:48:00Z", now, singapore)).toBe(
      "You last talked with Zeph today.",
    );
    expect(lastTalkedText("2026-11-10T11:48:00Z", now, singapore)).toBe(
      "You last talked with Zeph yesterday.",
    );
    expect(lastTalkedText("2026-11-02T01:05:00Z", now, singapore)).toBe(
      "You last talked with Zeph on 2 Nov.",
    );
    expect(lastTalkedText(null, now, singapore)).toBe(
      "You haven't talked with Zeph yet.",
    );
  });

  it("says how often Check-ins come, as the choice is named", () => {
    expect(checkInFrequencyText("few_times_a_week")).toBe("A few times a week");
    expect(checkInFrequencyText("weekly")).toBe("Weekly");
  });

  it("writes quiet hours as times of day", () => {
    expect(quietHoursText("23:00:00", "07:00:00")).toBe("11:00 PM to 7:00 AM");
    expect(quietHoursText("22:00:00", "07:30:00")).toBe("10:00 PM to 7:30 AM");
  });

  it("names the day of the last Check-in, and whether the User replied", () => {
    const now = new Date("2026-11-17T12:00:00Z");

    expect(lastCheckInText(checkInWith(), now, singapore)).toBe(
      "Tuesday · you replied",
    );
    expect(
      lastCheckInText(checkInWith({ status: "no_reply" }), now, singapore),
    ).toBe("Tuesday · no reply");
    expect(
      lastCheckInText(
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
    expect(lastCheckInText(null, new Date(), singapore)).toBe("None yet");
  });
});
