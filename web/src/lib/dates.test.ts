import { describe, expect, it } from "vitest";

import { formatDay, formatSavedAt } from "@/lib/dates";

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
