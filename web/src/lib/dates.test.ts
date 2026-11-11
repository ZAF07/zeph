import { describe, expect, it } from "vitest";

import {
  formatDay,
  formatSavedAt,
  formatShortDay,
  formatWeekdayDay,
} from "@/lib/dates";

describe("formatDay", () => {
  it("writes a day the way the admin tables show it", () => {
    expect(formatDay("2026-10-02T09:00:00Z", "UTC")).toBe("2 Oct 2026");
  });

  it("uses the given time zone", () => {
    expect(formatDay("2026-10-02T20:00:00Z", "Asia/Singapore")).toBe(
      "3 Oct 2026",
    );
  });
});

describe("formatSavedAt", () => {
  it("writes the day and time something was saved", () => {
    expect(formatSavedAt("2026-11-08T14:20:00Z", "UTC")).toBe("8 Nov, 14:20");
  });
});

describe("formatShortDay", () => {
  it("writes the day and month a memory came from", () => {
    expect(formatShortDay("2026-10-02T09:00:00Z", "UTC")).toBe("2 Oct");
  });
});

describe("formatWeekdayDay", () => {
  it("writes the weekday, day and month of a Conversation Summary", () => {
    expect(formatWeekdayDay("2026-11-11T09:00:00Z", "UTC")).toBe("Wed 11 Nov");
  });

  it("uses the given time zone", () => {
    expect(formatWeekdayDay("2026-11-11T20:00:00Z", "Asia/Singapore")).toBe(
      "Thu 12 Nov",
    );
  });
});
