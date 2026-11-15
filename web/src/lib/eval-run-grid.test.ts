import { describe, expect, it } from "vitest";

import type { CaseResult } from "@/lib/api-client";
import {
  cellKey,
  describeTriesUsage,
  resultsByCell,
  triesPill,
} from "@/lib/eval-run-grid";
import { passedResult } from "@/test/eval-runs";

function tryOf(tryNumber: number, outcome: CaseResult["outcome"]): CaseResult {
  return {
    ...passedResult,
    id: `r-${tryNumber}`,
    try_number: tryNumber,
    outcome,
  };
}

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

describe("describeTriesUsage", () => {
  it("adds up a cell's tokens and time", () => {
    expect(describeTriesUsage([tryOf(1, "pass"), tryOf(2, "fail")])).toBe(
      "1,800 in / 80 out · 4.8 s",
    );
  });
});
