import { describe, expect, it } from "vitest";

import type { MoveInput } from "@/lib/api-client";
import { isMoveChanged, isMoveComplete, moveInputOf } from "@/lib/move-draft";

const saved: MoveInput = {
  name: "Research",
  when_it_fits: "They need facts.",
  how_to_do_it: "Look it up.",
  needed_feature: null,
  asks_a_question: false,
};

describe("isMoveChanged", () => {
  it("is false for the saved Move", () => {
    expect(isMoveChanged({ ...saved }, saved)).toBe(false);
  });

  it("sees a changed Feature or question mark", () => {
    expect(
      isMoveChanged({ ...saved, needed_feature: "web_search" }, saved),
    ).toBe(true);
    expect(isMoveChanged({ ...saved, asks_a_question: true }, saved)).toBe(
      true,
    );
  });
});

describe("isMoveComplete", () => {
  it("needs a name and both texts", () => {
    expect(isMoveComplete(saved)).toBe(true);
    expect(isMoveComplete({ ...saved, how_to_do_it: "" })).toBe(false);
  });
});

describe("moveInputOf", () => {
  it("leaves out the id", () => {
    expect(moveInputOf({ ...saved, id: "m1" } as MoveInput)).toEqual(saved);
  });
});
