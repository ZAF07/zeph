import { describe, expect, it } from "vitest";

import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInFrequencyChoices,
  checkInStatusText,
  formatCheckInDay,
  formatQuietHour,
  formatTimeOfDay,
  pausedText,
  recentCheckInTitle,
  toTimeFieldValue,
} from "@/lib/check-ins";
import { seedCopy } from "@/test/copy";

const copy = seedCopy();

function recentCheckIn(overrides: Partial<RecentCheckIn> = {}): RecentCheckIn {
  return {
    id: "check-in-1",
    outcome: "skipped",
    kind: null,
    decided_at: "2026-11-12T09:00:00Z",
    status: "skipped",
    skipped_for_daily_limit: false,
    ...overrides,
  };
}

describe("check-in wording", () => {
  it("says a limit skip happened because the User reached today's message limit", () => {
    expect(
      recentCheckInTitle(
        copy,
        recentCheckIn({ skipped_for_daily_limit: true }),
      ),
    ).toBe("Skipped — you’d reached today’s message limit");
  });

  it("says any other skip gave the User some space", () => {
    expect(recentCheckInTitle(copy, recentCheckIn())).toBe(
      "Zeph gave you space",
    );
  });

  it("names a sent Check-in by its Kind, or as a check-in when it has none", () => {
    const sent = { outcome: "sent", status: "replied" } as const;

    expect(
      recentCheckInTitle(copy, recentCheckIn({ ...sent, kind: "A hello" })),
    ).toBe("A hello");
    expect(recentCheckInTitle(copy, recentCheckIn(sent))).toBe("A check-in");
    expect(
      recentCheckInTitle(
        copy,
        recentCheckIn({ outcome: "asked_about_fewer", status: "sent" }),
      ),
    ).toBe("Asked if you’d like fewer");
  });

  it("takes each line from Copy", () => {
    const adminCopy = {
      ...copy,
      "check_ins.recent.gave_space": "Zeph let you be",
      "check_ins.paused.title_until_day": "Paused till {day}",
      "check_ins.recent.no_reply": "Unanswered",
      "onboarding.check_ins.frequency_weekly": "Once a week",
    };

    expect(recentCheckInTitle(adminCopy, recentCheckIn())).toBe(
      "Zeph let you be",
    );
    expect(pausedText(adminCopy, "2026-11-11T17:00:00Z", "UTC")).toBe(
      "Paused till 11 Nov",
    );
    expect(checkInStatusText(adminCopy, "no_reply")).toBe("Unanswered");
    expect(checkInFrequencyChoices(adminCopy)[0]).toEqual({
      value: "weekly",
      label: "Once a week",
    });
  });

  it("names each Check-in status", () => {
    expect(checkInStatusText(copy, "sent")).toBe("Sent");
    expect(checkInStatusText(copy, "replied")).toBe("Replied");
    expect(checkInStatusText(copy, "no_reply")).toBe("No reply");
    expect(checkInStatusText(copy, "skipped")).toBe("Skipped");
  });

  it("names the frequencies with onboarding's words, in order", () => {
    expect(checkInFrequencyChoices(copy)).toEqual([
      { value: "weekly", label: "Weekly" },
      { value: "few_times_a_week", label: "A few times a week" },
      { value: "most_days", label: "Most days" },
      { value: "a_few_times_a_day", label: "A few times a day" },
    ]);
  });

  it("writes a quiet hours time of day like 11:00 PM", () => {
    expect(formatQuietHour("23:00:00")).toBe("11:00 PM");
    expect(formatQuietHour("07:30:00")).toBe("7:30 AM");
  });

  it("turns a backend time of day into a time field value", () => {
    expect(toTimeFieldValue("22:00:00")).toBe("22:00");
  });

  it("says when a timed pause ends, in the User's time zone", () => {
    expect(pausedText(copy, "2026-11-11T17:00:00Z", "Asia/Singapore")).toBe(
      "Check-ins are paused until 12 Nov",
    );
  });

  it("says a pause lasts until the User resumes", () => {
    expect(pausedText(copy, null)).toBe(
      "Check-ins are paused until you resume",
    );
  });

  it("writes the day of a Check-in with its weekday, without a time", () => {
    expect(formatCheckInDay("2026-11-06T17:00:00Z", "Asia/Singapore")).toBe(
      "Saturday 7 Nov",
    );
  });

  it("writes a time of day in the User's time zone", () => {
    expect(formatTimeOfDay("2026-11-11T11:48:00Z", "Asia/Singapore")).toBe(
      "7:48 pm",
    );
  });
});
