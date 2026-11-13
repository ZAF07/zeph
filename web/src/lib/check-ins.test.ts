import { describe, expect, it } from "vitest";

import {
  formatCheckInDay,
  formatCheckInSentAt,
  formatTimeOfDay,
  pauseEndText,
  pausedText,
  recentCheckInTitle,
  toTimeFieldValue,
} from "@/lib/check-ins";

describe("check-in wording", () => {
  it("says a limit skip happened because the User reached today's message limit", () => {
    expect(
      recentCheckInTitle({
        id: "check-in-1",
        outcome: "skipped",
        kind: null,
        decided_at: "2026-11-12T09:00:00Z",
        status: "skipped",
        skipped_for_daily_limit: true,
      }),
    ).toBe("Skipped — you’d reached today’s message limit");
  });

  it("says any other skip gave the User some space", () => {
    expect(
      recentCheckInTitle({
        id: "check-in-1",
        outcome: "skipped",
        kind: null,
        decided_at: "2026-11-12T09:00:00Z",
        status: "skipped",
        skipped_for_daily_limit: false,
      }),
    ).toBe("Skipped — gave you some space");
  });

  it("turns a backend time of day into a time field value", () => {
    expect(toTimeFieldValue("22:00:00")).toBe("22:00");
  });

  it("says when a timed pause ends, in the User's time zone", () => {
    expect(pausedText("2026-11-11T17:00:00Z", "Asia/Singapore")).toBe(
      "Paused until Thursday, 12 November.",
    );
  });

  it("says a pause lasts until the User resumes", () => {
    expect(pausedText(null)).toBe("Paused until you resume.");
  });

  it("writes when a Check-in was sent", () => {
    expect(formatCheckInSentAt("2026-11-09T10:42:00Z", "Asia/Singapore")).toBe(
      "Mon 9 Nov · 6:42 pm",
    );
  });

  it("writes the day of a skipped Check-in, without a time", () => {
    expect(formatCheckInDay("2026-11-06T17:00:00Z", "Asia/Singapore")).toBe(
      "Sat 7 Nov",
    );
  });

  it("says when a pause ends without the word Paused", () => {
    expect(pauseEndText("2026-11-11T17:00:00Z", "Asia/Singapore")).toBe(
      "until Thursday, 12 November",
    );
    expect(pauseEndText(null)).toBe("until you resume");
  });

  it("writes a time of day in the User's time zone", () => {
    expect(formatTimeOfDay("2026-11-11T11:48:00Z", "Asia/Singapore")).toBe(
      "7:48 pm",
    );
  });
});
