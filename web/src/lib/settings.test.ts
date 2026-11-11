import { describe, expect, it } from "vitest";

import type { AdminSettings } from "@/lib/api-client";
import { lastSavedNote, textSetting } from "@/lib/settings";

const settings: AdminSettings = {
  persona: {
    value: "You are Zeph.",
    updated_at: "2026-11-08T14:20:00Z",
    updated_by: "Maya Lin",
  },
  response_prompt: {
    value: "Reply briefly.",
    updated_at: "2026-11-09T08:05:00Z",
    updated_by: "Ren Okafor",
  },
  conversation_quiet_gap_minutes: {
    value: 60,
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  },
};

describe("textSetting", () => {
  it("reads a setting's value as text", () => {
    expect(textSetting(settings, "persona")).toBe("You are Zeph.");
    expect(textSetting(settings, "conversation_quiet_gap_minutes")).toBe("60");
  });

  it("gives empty text for a setting that is missing", () => {
    expect(textSetting(settings, "missing")).toBe("");
  });
});

describe("lastSavedNote", () => {
  it("names the newest save among the given settings and who made it", () => {
    expect(lastSavedNote(settings, ["persona", "response_prompt"], "UTC")).toBe(
      "Last saved 9 Nov, 08:05 by Ren Okafor",
    );
  });

  it("says the starting values are in use when no Admin has saved them", () => {
    expect(
      lastSavedNote(settings, ["conversation_quiet_gap_minutes"], "UTC"),
    ).toBe("Using the starting values");
  });
});
