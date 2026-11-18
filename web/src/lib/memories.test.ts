import { describe, expect, it } from "vitest";

import { memoriesTabFromQuery, searchWithMemoriesTab } from "@/lib/memories";

describe("memoriesTabFromQuery", () => {
  it.each([
    ["about", "about"],
    ["threads", "threads"],
    ["helps", "helps"],
    ["summaries", "summaries"],
    ["photos", "photos"],
  ])("picks the %s tab", (value, tab) => {
    expect(memoriesTabFromQuery(value)).toBe(tab);
  });

  it.each([null, "", "nonsense", "memories"])(
    "falls back to the Memories tab for %j",
    (value) => {
      expect(memoriesTabFromQuery(value)).toBe("memories");
    },
  );
});

describe("searchWithMemoriesTab", () => {
  it("sets the tab", () => {
    expect(searchWithMemoriesTab("", "photos")).toBe("?tab=photos");
  });

  it("replaces the tab and keeps other values", () => {
    expect(searchWithMemoriesTab("?design=menu-open&tab=about", "helps")).toBe(
      "?design=menu-open&tab=helps",
    );
  });

  it("drops the tab for the Memories tab", () => {
    expect(searchWithMemoriesTab("?tab=about", "memories")).toBe("");
    expect(
      searchWithMemoriesTab("?tab=about&design=menu-open", "memories"),
    ).toBe("?design=menu-open");
  });
});
