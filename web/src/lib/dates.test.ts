import { describe, expect, it } from "vitest";

import {
  formatAddedDay,
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

describe("formatAddedDay", () => {
  const now = new Date("2026-11-12T10:00:00Z");

  it("says Today and Yesterday for the last two days", () => {
    expect(formatAddedDay("2026-11-12T01:00:00Z", now, "UTC")).toBe("Today");
    expect(formatAddedDay("2026-11-11T23:59:00Z", now, "UTC")).toBe(
      "Yesterday",
    );
  });

  it("writes the day and month for anything older", () => {
    expect(formatAddedDay("2026-10-02T09:00:00Z", now, "UTC")).toBe("2 Oct");
  });

  it("counts days in the given time zone", () => {
    expect(formatAddedDay("2026-11-11T17:00:00Z", now, "Asia/Singapore")).toBe(
      "Today",
    );
  });
});
