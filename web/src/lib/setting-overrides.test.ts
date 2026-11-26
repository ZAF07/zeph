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
      hint: "",
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
  moves: [
    {
      key: "move:1",
      name: "Research",
      value: { name: "Research", when_it_fits: "w", how_to_do_it: "h" },
    },
  ],
  models: ["deepseek-flash"],
};

describe("overrideLabel", () => {
  it("names settings by their label and Needs and Moves by their name", () => {
    expect(overrideLabel("understanding_thinking", choices)).toBe(
      "Understanding thinking",
    );
    expect(overrideLabel("need:1", choices)).toBe("Need: Be heard");
    expect(overrideLabel("need:2", choices)).toBe("Need: a Need deleted since");
    expect(overrideLabel("move:1", choices)).toBe("Move: Research");
    expect(overrideLabel("move:2", choices)).toBe("Move: a Move deleted since");
    expect(overrideLabel("unknown_key", undefined)).toBe("unknown_key");
  });

  it("names a Need or Move by its name when the run started first", () => {
    const then = {
      needs: [
        {
          key: "need:1",
          name: "Be listened to",
          value: {
            name: "Be listened to",
            when_it_fits: "w",
            how_to_reply: "h",
          },
        },
      ],
      moves: [
        {
          key: "move:2",
          name: "Look it up",
          value: { name: "Look it up", when_it_fits: "w", how_to_do_it: "h" },
        },
      ],
    };

    expect(overrideLabel("need:1", choices, then)).toBe("Need: Be listened to");
    expect(overrideLabel("move:2", choices, then)).toBe("Move: Look it up");
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
    expect(
      describeSettingValue({
        name: "Be heard",
        when_it_fits: "venting",
        how_to_reply: "listen",
        curiosities: "never",
      }),
    ).toBe(
      "Be heard\nWhen it fits: venting\nHow to reply: listen\nCuriosities: Never",
    );
    expect(
      describeSettingValue({
        name: "Research",
        when_it_fits: "they need options",
        how_to_do_it: "search",
      }),
    ).toBe("Research\nWhen it fits: they need options\nHow to do it: search");
  });
});

describe("describeVariantSettings", () => {
  it("says how many settings a Variant changes", () => {
    expect(describeVariantSettings(0)).toBe("live settings");
    expect(describeVariantSettings(2)).toBe("live settings with 2 changed");
  });
});
