import { describe, expect, it } from "vitest";

import {
  formatCheckInDay,
  formatCheckInSentAt,
  pausedText,
  toTimeFieldValue,
} from "@/lib/check-ins";

describe("check-in wording", () => {
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
});
