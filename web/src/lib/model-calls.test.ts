import { describe, expect, it } from "vitest";

import {
  describeSteps,
  formatDuration,
  modelStepLabel,
  traceKindLabel,
} from "@/lib/model-calls";

describe("model call labels", () => {
  it("names steps and trace kinds in plain words", () => {
    expect(modelStepLabel("memory_picking")).toBe("Memory picking");
    expect(traceKindLabel("conversation_end")).toBe("Conversation end");
  });

  it("writes short times in milliseconds and longer ones in seconds", () => {
    expect(formatDuration(850)).toBe("850 ms");
    expect(formatDuration(2400)).toBe("2.4 s");
  });

  it("lists each step once, with how many times a retried one ran", () => {
    expect(describeSteps(["safeguard", "safeguard", "reply"])).toBe(
      "Safeguard ×2 → Reply",
    );
  });
});
