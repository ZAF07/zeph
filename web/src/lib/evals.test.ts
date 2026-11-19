import { describe, expect, it } from "vitest";

import { evalCaseEditHref, evalCasesHref } from "@/lib/evals";

describe("eval case addresses", () => {
  it("points at one Eval's cases", () => {
    expect(evalCasesHref("persona")).toBe("/admin/evals/cases/persona");
  });

  it("points at a case's editor", () => {
    expect(evalCaseEditHref({ eval: "persona", key: "small-talk" })).toBe(
      "/admin/evals/cases/persona/edit/small-talk",
    );
  });
});
