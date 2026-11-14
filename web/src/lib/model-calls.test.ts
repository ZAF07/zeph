import { describe, expect, it } from "vitest";

import {
  describeSteps,
  formatDuration,
  formatTokens,
  modelStepLabel,
  traceKindLabel,
} from "@/lib/model-calls";

describe("model call labels", () => {
  it("names steps and trace kinds in plain words", () => {
    expect(modelStepLabel("understanding")).toBe("Understanding");
    expect(traceKindLabel("conversation_end")).toBe("Conversation end");
  });

  it("writes short times in milliseconds and longer ones in seconds", () => {
    expect(formatDuration(850)).toBe("850 ms");
    expect(formatDuration(2400)).toBe("2.4 s");
  });

  it("writes tokens in and out with thousands separators", () => {
    expect(formatTokens(1200, 80)).toBe("1,200 in / 80 out");
  });

  it("lists each step once, with how many times a retried one ran", () => {
    expect(describeSteps(["safeguard", "safeguard", "reply"])).toBe(
      "Safeguard ×2 → Reply",
    );
  });
});
