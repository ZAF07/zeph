import { describe, expect, it } from "vitest";

import {
  describeSteps,
  formatDuration,
  formatTokens,
  modelStepLabel,
  traceKindLabel,
  understandingShapeFacts,
} from "@/lib/model-calls";

describe("model call labels", () => {
  it("names steps and trace kinds in plain words", () => {
    expect(modelStepLabel("understanding")).toBe("Understanding");
    expect(modelStepLabel("life_threads")).toBe("Life Threads");
    expect(traceKindLabel("conversation_end")).toBe("Conversation end");
    expect(modelStepLabel("portrait")).toBe("User Portrait");
    expect(traceKindLabel("portrait_rewrite")).toBe("Portrait rewrite");
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

  it("writes an Understanding with no Threads brought up as 0", () => {
    const facts = understandingShapeFacts({
      need: "Ask more",
      intensity: "low",
      cause_known: true,
      threads_reminded: 0,
      threads_led_with: 0,
      threads_woven_in: 0,
      threads_left_alone: 0,
      threads_held_back: 0,
      past_look_ups: 0,
    });
    expect(facts).toContainEqual({ label: "Threads brought up", value: "0" });
    expect(facts).toContainEqual({ label: "Cause known", value: "Yes" });
    expect(facts).toContainEqual({ label: "Mood intensity", value: "Low" });
  });
});
