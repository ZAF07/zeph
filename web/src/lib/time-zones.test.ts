import { describe, expect, it } from "vitest";

import { timeZoneLabel, timeZoneOptions } from "@/lib/time-zones";

describe("timeZoneLabel", () => {
  it("shows the place and its GMT offset", () => {
    expect(timeZoneLabel("Asia/Singapore")).toBe("Singapore (GMT+8)");
  });

  it("turns underscores into spaces", () => {
    expect(timeZoneLabel("Asia/Kuala_Lumpur")).toBe("Kuala Lumpur (GMT+8)");
  });
});

describe("timeZoneOptions", () => {
  it("includes an extra time zone the browser list lacks", () => {
    const names = timeZoneOptions("UTC").map((option) => option.name);

    expect(names).toContain("UTC");
    expect(names).toContain("Europe/London");
  });
});
