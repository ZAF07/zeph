import { describe, expect, it } from "vitest";

import type { PatternType } from "@/lib/api-client";
import { describeSignature, describeStatus } from "@/lib/pattern-catalog";
import { patternType } from "@/test/pattern-type";

const approved: PatternType = {
  ...patternType,
  status: "approved",
  approved_by: "Zaf",
  approved_on: "2026-11-24",
};

describe("describeSignature", () => {
  it("joins the situation, the behaviour and what it gets them", () => {
    expect(describeSignature(patternType)).toBe(
      "Disagreement with a valued other → Withholds or softens own view → To protect belonging",
    );
  });
});

describe("describeStatus", () => {
  it("says a draft gathers evidence and is never shared", () => {
    expect(describeStatus(patternType)).toBe(
      "Draft. Gathers evidence, never shared.",
    );
  });

  it("says who approved an approved one and when", () => {
    expect(describeStatus(approved)).toBe(
      "Approved by Zaf on 24 Nov 2026. May be shared once ready.",
    );
  });

  it("says an archived one is no longer used, keeping its approval", () => {
    expect(describeStatus({ ...approved, status: "archived" })).toBe(
      "Archived. Approved by Zaf on 24 Nov 2026. No longer used.",
    );
    expect(describeStatus({ ...patternType, status: "archived" })).toBe(
      "Archived. No longer used.",
    );
  });
});
