import { describe, expect, it } from "vitest";

import type { NeedInput } from "@/lib/api-client";
import { isNeedChanged, isNeedComplete, needInputOf } from "@/lib/need-draft";

const saved: NeedInput = {
  name: "Advice",
  when_it_fits: "They ask what to do.",
  how_to_reply: "One idea.",
  ruled_out_move_ids: ["calm", "push"],
  curiosities: "only_if_it_fits",
};

describe("isNeedChanged", () => {
  it("ignores the order of the rule-outs", () => {
    expect(
      isNeedChanged({ ...saved, ruled_out_move_ids: ["push", "calm"] }, saved),
    ).toBe(false);
  });

  it("sees an added or dropped rule-out", () => {
    expect(
      isNeedChanged({ ...saved, ruled_out_move_ids: ["calm"] }, saved),
    ).toBe(true);
    expect(
      isNeedChanged(
        { ...saved, ruled_out_move_ids: ["calm", "mirror"] },
        saved,
      ),
    ).toBe(true);
  });

  it("sees a changed Curiosities choice", () => {
    expect(isNeedChanged({ ...saved, curiosities: "never" }, saved)).toBe(true);
  });

  it("sees a changed text", () => {
    expect(isNeedChanged({ ...saved, how_to_reply: "Two ideas." }, saved)).toBe(
      true,
    );
  });
});

describe("isNeedComplete", () => {
  it("needs a name and both texts", () => {
    expect(isNeedComplete(saved)).toBe(true);
    expect(isNeedComplete({ ...saved, when_it_fits: "  " })).toBe(false);
  });
});

describe("needInputOf", () => {
  it("leaves out the id and fallback mark", () => {
    expect(
      needInputOf({ ...saved, id: "n1", is_fallback: true } as NeedInput),
    ).toEqual(saved);
  });
});
