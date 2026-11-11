import { describe, expect, it } from "vitest";

import { paragraphs } from "@/lib/paragraphs";

describe("paragraphs", () => {
  it("splits at blank lines and drops empty ones", () => {
    expect(paragraphs("One\nstill one.\n\n\nTwo.\n\n  ")).toEqual([
      "One\nstill one.",
      "Two.",
    ]);
  });
});
