import { describe, expect, it } from "vitest";

import type { OverrideChoices } from "@/lib/api-client";
import {
  describeSettingValue,
  describeVariantSettings,
  overrideLabel,
} from "@/lib/setting-overrides";

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

describe("describeVariantSettings", () => {
  it("says how many settings a Variant changes", () => {
    expect(describeVariantSettings(0)).toBe("live settings");
    expect(describeVariantSettings(2)).toBe("live settings with 2 changed");
  });
});
