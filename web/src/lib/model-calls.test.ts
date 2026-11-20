import { describe, expect, it } from "vitest";

import {
  describeSteps,
  formatDuration,
  formatTokens,
  modelStepLabel,
  traceKindLabel,
  replyPlanShapeFacts,
  understandingShapeFacts,
} from "@/lib/model-calls";

describe("model call labels", () => {
  it("names steps and trace kinds in plain words", () => {
    expect(modelStepLabel("understanding")).toBe("Understanding");
    expect(modelStepLabel("life_threads")).toBe("Life Threads");
    expect(modelStepLabel("move_outcomes")).toBe("Move Outcomes");
    expect(modelStepLabel("patterns")).toBe("Pattern keeping");
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

  it("writes an Understanding's intensity, cause, struggling and look-ups", () => {
    const facts = understandingShapeFacts({
      intensity: "high",
      cause_known: true,
      struggling: false,
      past_look_ups: 1,
    });
    expect(facts).toEqual([
      { label: "Mood intensity", value: "Strong" },
      { label: "Cause known", value: "Yes" },
      { label: "Struggling", value: "No" },
      { label: "Past look-ups", value: "1" },
    ]);
  });

  it("writes a Reply Plan with no Moves or Threads brought up", () => {
    const facts = replyPlanShapeFacts({
      need: "Ask more",
      lead_move: null,
      support_move: null,
      next_move: null,
      threads_reminded: 0,
      threads_led_with: 0,
      threads_woven_in: 0,
      threads_left_alone: 0,
      threads_held_back: 0,
    });
    expect(facts).toContainEqual({ label: "Need picked", value: "Ask more" });
    expect(facts).toContainEqual({ label: "Threads brought up", value: "0" });
    expect(facts).toContainEqual({ label: "Lead Move", value: "None" });
    expect(facts).toContainEqual({ label: "Supporting Move", value: "None" });
    expect(facts).toContainEqual({ label: "Next Move", value: "None" });
  });

  it("names the lead, supporting and next Moves a Reply Plan picked", () => {
    const facts = replyPlanShapeFacts({
      need: "Accountability",
      lead_move: "Research",
      support_move: "Suggest",
      next_move: "Plan steps",
      threads_reminded: 5,
      threads_led_with: 1,
      threads_woven_in: 0,
      threads_left_alone: 3,
      threads_held_back: 1,
    });
    expect(facts).toContainEqual({ label: "Lead Move", value: "Research" });
    expect(facts).toContainEqual({
      label: "Supporting Move",
      value: "Suggest",
    });
    expect(facts).toContainEqual({ label: "Next Move", value: "Plan steps" });
    expect(facts).toContainEqual({
      label: "Threads brought up",
      value: "1 (1 lead, 0 weave)",
    });
  });
});
