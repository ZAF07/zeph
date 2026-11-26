import { describe, expect, it } from "vitest";

import {
  curiosityTreatmentLabel,
  curiosityTreatmentOptions,
  toCuriosityTreatment,
} from "@/lib/curiosity-treatment";

describe("curiosity treatment", () => {
  it("offers the four choices in order", () => {
    expect(curiosityTreatmentOptions.map((option) => option.label)).toEqual([
      "Ask by default",
      "Test the water",
      "Only if it fits",
      "Never",
    ]);
  });

  it("names a choice", () => {
    expect(curiosityTreatmentLabel("ask_by_default")).toBe("Ask by default");
    expect(curiosityTreatmentLabel("never")).toBe("Never");
    expect(curiosityTreatmentLabel("test_the_water")).toBe("Test the water");
  });

  it("reads a picked choice, and an unknown one as only if it fits", () => {
    expect(toCuriosityTreatment("never")).toBe("never");
    expect(toCuriosityTreatment("always")).toBe("only_if_it_fits");
  });
});
