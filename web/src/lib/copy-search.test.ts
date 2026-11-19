import { describe, expect, it } from "vitest";

import type { CopySlot, CopyTab } from "@/lib/api-client";
import { searchCopySlots } from "@/lib/copy-search";

function slot(key: string, text: string): CopySlot {
  return {
    key,
    name: key,
    text,
    max_length: 80,
    placeholders: [],
    updated_at: "2026-11-11T09:00:00Z",
    updated_by: null,
  };
}

const tabs: CopyTab[] = [
  {
    tab: "landing",
    name: "Landing",
    slots: [
      slot("landing.heading", "Think Deeper,"),
      slot("landing.body", "A companion that remembers."),
    ],
  },
  {
    tab: "pricing",
    name: "Pricing",
    slots: [slot("pricing.lead", "Plans that remember you.")],
  },
];

describe("searchCopySlots", () => {
  it("finds slots in every tab whose text holds the words, in tab and page order", () => {
    expect(
      searchCopySlots(tabs, "remember").map((match) => [
        match.tab.tab,
        match.slot.key,
      ]),
    ).toEqual([
      ["landing", "landing.body"],
      ["pricing", "pricing.lead"],
    ]);
  });

  it("ignores letter case and the spaces around the words", () => {
    expect(
      searchCopySlots(tabs, "  think deeper ").map((match) => match.slot.key),
    ).toEqual(["landing.heading"]);
  });

  it("finds nothing for an empty search", () => {
    expect(searchCopySlots(tabs, "   ")).toEqual([]);
  });

  it("finds nothing when no text holds the words", () => {
    expect(searchCopySlots(tabs, "billing")).toEqual([]);
  });
});
