import { describe, expect, it } from "vitest";

import { MissingCopyError } from "@/lib/copy";
import { memoryOffNote } from "@/lib/memory-off-note";

const copy = {
  "shared.memory_off.paused_title": "Memory is paused.",
  "shared.memory_off.paused_body": "Nothing is deleted.",
  "shared.memory_off.not_available_title": "Memory isn’t available.",
  "shared.memory_off.not_available_body": "Ask an Admin.",
};

describe("memoryOffNote", () => {
  it("is nothing while User Memory works", () => {
    expect(
      memoryOffNote(copy, {
        user_memory_enabled: true,
        user_memory_available: true,
      }),
    ).toBeNull();
  });

  it("says Memory is paused while the User has it off", () => {
    expect(
      memoryOffNote(copy, {
        user_memory_enabled: false,
        user_memory_available: true,
      }),
    ).toEqual({ title: "Memory is paused.", body: "Nothing is deleted." });
  });

  it("says Memory isn't available while an Admin has it off, whatever the User's switch", () => {
    const notAvailable = {
      title: "Memory isn’t available.",
      body: "Ask an Admin.",
    };
    expect(
      memoryOffNote(copy, {
        user_memory_enabled: true,
        user_memory_available: false,
      }),
    ).toEqual(notAvailable);
    expect(
      memoryOffNote(copy, {
        user_memory_enabled: false,
        user_memory_available: false,
      }),
    ).toEqual(notAvailable);
  });

  it("throws when the Copy has no such slot", () => {
    expect(() =>
      memoryOffNote(
        {},
        { user_memory_enabled: false, user_memory_available: true },
      ),
    ).toThrow(MissingCopyError);
  });
});
