import { describe, expect, it } from "vitest";

import { riskTypeLabel } from "@/lib/risk-types";

describe("riskTypeLabel", () => {
  it("names each risk type in plain words", () => {
    expect(riskTypeLabel("suicide_or_self_harm")).toBe("Suicide / self-harm");
    expect(riskTypeLabel("medical_emergency")).toBe("Medical emergency");
    expect(riskTypeLabel("unclear")).toBe("Unclear answer");
  });
});
