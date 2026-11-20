import { describe, expect, it } from "vitest";

import {
  personaTabDetails,
  personaTabFromQuery,
  personaTabs,
  searchWithPersonaTab,
} from "@/lib/persona";

describe("personaTabFromQuery", () => {
  it("reads the Outlook tab and falls back to Voice for anything else", () => {
    expect(personaTabFromQuery("outlook")).toBe("outlook");
    expect(personaTabFromQuery("voice")).toBe("voice");
    expect(personaTabFromQuery("memories")).toBe("voice");
    expect(personaTabFromQuery(["outlook", "voice"])).toBe("voice");
    expect(personaTabFromQuery(null)).toBe("voice");
    expect(personaTabFromQuery(undefined)).toBe("voice");
  });
});

describe("searchWithPersonaTab", () => {
  it("sets the Outlook tab and keeps other query values", () => {
    expect(searchWithPersonaTab("?design=menu-open", "outlook")).toBe(
      "?design=menu-open&tab=outlook",
    );
  });

  it("leaves no tab value for Voice", () => {
    expect(searchWithPersonaTab("?tab=outlook", "voice")).toBe("");
    expect(searchWithPersonaTab("?tab=outlook&design=menu-open", "voice")).toBe(
      "?design=menu-open",
    );
  });
});

describe("personaTabs", () => {
  it("lists Voice then Outlook, each editing its own setting", () => {
    expect(personaTabs.map((tab) => [tab.name, tab.settingKey])).toEqual([
      ["Voice", "persona"],
      ["Outlook", "persona_outlook"],
    ]);
    expect(personaTabDetails("outlook").saveLabel).toBe("Save Outlook");
  });
});
