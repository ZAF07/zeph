import { describe, expect, it } from "vitest";

import { lastChangeNote, reasonText } from "@/lib/features";

describe("lastChangeNote", () => {
  it("says a switch was never changed", () => {
    expect(lastChangeNote({ changed_at: null, changed_by_email: null })).toBe(
      "Never changed",
    );
  });

  it("names who changed it and when", () => {
    expect(
      lastChangeNote({
        changed_at: "2026-11-13T09:00:00Z",
        changed_by_email: "maya@example.com",
      }),
    ).toMatch(/^Changed 13 Nov, .+ by maya@example\.com$/);
  });
});

describe("reasonText", () => {
  it("explains a Feature turned off for one User", () => {
    expect(reasonText("off_for_user")).toBe("Off: turned off for this User");
  });
});
