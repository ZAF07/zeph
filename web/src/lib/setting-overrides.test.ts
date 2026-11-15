import { describe, expect, it } from "vitest";

import type { CaseResult, OverrideChoices } from "@/lib/api-client";
import {
  cellKey,
  describeSettingValue,
  overrideLabel,
  resultsByCell,
  triesPill,
} from "@/lib/setting-overrides";
import { passedResult } from "@/test/eval-runs";

const choices: OverrideChoices = {
  settings: [
    {
      key: "understanding_thinking",
      label: "Understanding thinking",
      kind: "on_off",
      minimum: 0,
      maximum: 0,
      max_length: 20000,
      hint: null,
      value: true,
    },
  ],
  needs: [
    {
      key: "need:1",
      name: "Be heard",
      value: { name: "Be heard", when_it_fits: "w", how_to_reply: "h" },
    },
  ],
  models: ["deepseek-flash"],
};

function tryOf(tryNumber: number, outcome: CaseResult["outcome"]): CaseResult {
  return {
    ...passedResult,
    id: `r-${tryNumber}`,
    try_number: tryNumber,
    outcome,
  };
}

describe("overrideLabel", () => {
  it("names settings by their label and Needs by their name", () => {
    expect(overrideLabel("understanding_thinking", choices, [])).toBe(
      "Understanding thinking",
    );
    expect(overrideLabel("need:1", choices, [])).toBe("Need: Be heard");
    expect(overrideLabel("need:2", choices, [])).toBe(
      "Need: a Need deleted since",
    );
    expect(overrideLabel("unknown_key", undefined, [])).toBe("unknown_key");
  });
});

describe("describeSettingValue", () => {
  it("writes on/off, numbers, text and a Need's details", () => {
    expect(describeSettingValue(true)).toBe("On");
    expect(describeSettingValue(1200)).toBe("1,200");
    expect(describeSettingValue("Warm.")).toBe("Warm.");
    expect(describeSettingValue(null)).toBe("—");
    expect(
      describeSettingValue({
        name: "Be heard",
        when_it_fits: "venting",
        how_to_reply: "listen",
      }),
    ).toBe("Be heard\nWhen it fits: venting\nHow to reply: listen");
  });
});

describe("resultsByCell and triesPill", () => {
  it("groups tries per case and Variant in try order and counts the passes", () => {
    const cells = resultsByCell([
      tryOf(2, "fail"),
      tryOf(1, "pass"),
      { ...tryOf(1, "pass"), variant: "B" },
    ]);

    const tries = cells.get(cellKey("plan", "A")) ?? [];
    expect(tries.map((result) => result.try_number)).toEqual([1, 2]);
    expect(triesPill(tries, 3).label).toBe("1 of 3 passed");
    expect(triesPill(tries, 3).pill).toContain("danger");
    expect(triesPill([tryOf(1, "error")], 1).label).toBe("Error");
    expect(cells.get(cellKey("plan", "B"))).toHaveLength(1);
  });
});
