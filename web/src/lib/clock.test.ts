import { describe, expect, it } from "vitest";

import { currentTime } from "@/lib/clock";
import { greeting } from "@/lib/home";

describe("currentTime", () => {
  it("stands still at an evening in Singapore on design fixtures", () => {
    const now = currentTime(true);

    expect(now.toISOString()).toBe("2026-11-17T12:00:00.000Z");
    expect(greeting("Alex", now, "Asia/Singapore")).toBe("Good evening, Alex.");
  });

  it("tells the real time otherwise", () => {
    const before = Date.now();

    expect(currentTime(false).getTime()).toBeGreaterThanOrEqual(before);
  });
});
