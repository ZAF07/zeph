import { describe, expect, it } from "vitest";

import type { CopySlot } from "@/lib/api-client";
import { copySlotRows } from "@/lib/copy-slot-rows";

function slot(key: string): CopySlot {
  return {
    key,
    name: key,
    text: key,
    max_length: 80,
    placeholders: [],
    updated_at: "2026-11-11T09:00:00Z",
    updated_by: null,
  };
}

function rowKeys(slots: CopySlot[]): string[][] {
  return copySlotRows(slots).map((row) => row.map((found) => found.key));
}

describe("copySlotRows", () => {
  it("puts a one slot and the many slot after it in one row", () => {
    expect(
      rowKeys([
        slot("memories.heading"),
        slot("memories.confirm_body_one"),
        slot("memories.confirm_body_many"),
        slot("memories.keep"),
      ]),
    ).toEqual([
      ["memories.heading"],
      ["memories.confirm_body_one", "memories.confirm_body_many"],
      ["memories.keep"],
    ]);
  });

  it("keeps a one slot on its own row when the next slot isn't its many slot", () => {
    expect(
      rowKeys([
        slot("card.expires_one"),
        slot("card.waiting_many"),
        slot("card.expires_many"),
      ]),
    ).toEqual([
      ["card.expires_one"],
      ["card.waiting_many"],
      ["card.expires_many"],
    ]);
  });

  it("gives each other slot its own row, in page order", () => {
    expect(rowKeys([slot("a.first"), slot("a.second")])).toEqual([
      ["a.first"],
      ["a.second"],
    ]);
  });
});
