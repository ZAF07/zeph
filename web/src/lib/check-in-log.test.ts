import { describe, expect, it } from "vitest";

import type { CheckInLogEntry } from "@/lib/api-client";
import {
  filterCheckInLog,
  pausedReasonText,
  summarizeCheckInLog,
} from "@/lib/check-in-log";

function entry(overrides: Partial<CheckInLogEntry>): CheckInLogEntry {
  return {
    id: "entry",
    user_id: "user-1",
    user_name: "Maya Lin",
    user_email: "maya@example.com",
    decided_at: "2026-11-11T10:00:00Z",
    outcome: "sent",
    kind: "A casual hello",
    skip_reason: null,
    status: "no_reply",
    requested_by: null,
    woven_in: false,
    ...overrides,
  };
}

describe("Check-in log", () => {
  it("adds up sends, skips, replies and ignore-rule pauses", () => {
    expect(
      summarizeCheckInLog([
        entry({ status: "replied" }),
        entry({ status: "replied" }),
        entry({ status: "no_reply" }),
        entry({ status: "sent" }),
        entry({ outcome: "skipped", kind: null, status: "skipped" }),
        entry({ outcome: "asked_about_fewer", kind: null, status: "sent" }),
      ]),
    ).toEqual({
      sent: 4,
      skipped: 1,
      repliedPercent: 67,
      pausedByIgnoreRule: 1,
    });
  });

  it("has no reply rate until a send can be judged", () => {
    expect(
      summarizeCheckInLog([entry({ status: "sent" })]).repliedPercent,
    ).toBe(null);
  });

  it("filters by outcome and by the User's name or email", () => {
    const entries = [
      entry({ id: "maya-sent" }),
      entry({ id: "maya-skip", outcome: "skipped", status: "skipped" }),
      entry({ id: "ren-sent", user_name: "Ren", user_email: "ren@x.com" }),
    ];

    expect(
      filterCheckInLog(entries, "skipped", "").map((item) => item.id),
    ).toEqual(["maya-skip"]);
    expect(
      filterCheckInLog(entries, "all", "REN@").map((item) => item.id),
    ).toEqual(["ren-sent"]);
  });
});

describe("pausedReasonText", () => {
  it("names the Ignore Threshold in words up to ten", () => {
    expect(pausedReasonText(3)).toBe("Three in a row went unanswered");
    expect(pausedReasonText(5)).toBe("Five in a row went unanswered");
    expect(pausedReasonText(10)).toBe("Ten in a row went unanswered");
  });

  it("uses digits above ten", () => {
    expect(pausedReasonText(12)).toBe("12 in a row went unanswered");
  });

  it("says the ignore rule paused it when the threshold isn't known", () => {
    expect(pausedReasonText(null)).toBe("Paused by ignore rule");
  });
});
