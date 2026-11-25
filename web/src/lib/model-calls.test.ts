import { describe, expect, it } from "vitest";

import {
  describePatternUse,
  describeSteps,
  formatDuration,
  formatTokens,
  modelStepLabel,
  traceKindLabel,
  replyPlanShapeFacts,
  taggingShapeFacts,
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

  it("writes how many Curiosities a Reply Plan was offered and whether it asked one", () => {
    const facts = replyPlanShapeFacts({
      need: "Think it through",
      lead_move: null,
      support_move: null,
      next_move: null,
      threads_reminded: 0,
      threads_led_with: 0,
      threads_woven_in: 0,
      threads_left_alone: 0,
      threads_held_back: 0,
      read_formed: false,
      read_said: false,
      check_in_kinds_offered: 0,
      check_in_kind: null,
      pattern_used: false,
      pattern_offered: false,
      curiosities_offered: 2,
      curiosity_asked: true,
    });
    expect(facts.slice(-2)).toEqual([
      { label: "Curiosities offered", value: "2" },
      { label: "Curiosity asked", value: "Yes" },
    ]);
  });

  it("says what came of a ready Pattern the Reply Plan was offered", () => {
    const shape = {
      need: "Think it through",
      lead_move: null,
      support_move: null,
      next_move: null,
      threads_reminded: 0,
      threads_led_with: 0,
      threads_woven_in: 0,
      threads_left_alone: 0,
      threads_held_back: 0,
      read_formed: false,
      read_said: false,
      check_in_kinds_offered: 0,
      check_in_kind: null,
      pattern_used: false,
      pattern_offered: false,
    };
    const patternToShare = (
      offered: boolean,
      planned: boolean,
      shared: boolean | null,
    ) =>
      replyPlanShapeFacts({
        ...shape,
        pattern_to_share_offered: offered,
        pattern_share_planned: planned,
        pattern_shared: shared,
      }).find((fact) => fact.label === "Pattern to share")?.value;

    expect(patternToShare(false, false, null)).toBe("None offered");
    expect(patternToShare(true, false, null)).toBe("Offered, not picked");
    expect(patternToShare(true, true, null)).toBe("Picked");
    expect(patternToShare(true, true, false)).toBe("Picked, not shared");
    expect(patternToShare(true, true, true)).toBe("Shared");
    expect(replyPlanShapeFacts(shape).map((fact) => fact.label)).not.toContain(
      "Pattern to share",
    );
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
      read_formed: false,
      read_said: false,
      check_in_kinds_offered: 0,
      check_in_kind: null,
      pattern_used: false,
      pattern_offered: false,
    });
    expect(facts).toContainEqual({ label: "Need picked", value: "Ask more" });
    expect(facts.map((fact) => fact.label)).not.toContain(
      "Curiosities offered",
    );
    expect(facts).toContainEqual({ label: "Pattern", value: "None" });
    expect(facts).toContainEqual({ label: "Threads brought up", value: "0" });
    expect(facts).toContainEqual({ label: "Lead Move", value: "None" });
    expect(facts).toContainEqual({ label: "Supporting Move", value: "None" });
    expect(facts).toContainEqual({ label: "Next Move", value: "None" });
    expect(facts).toContainEqual({ label: "Read formed", value: "No" });
    expect(facts).toContainEqual({ label: "Read said", value: "No" });
    expect(facts).toContainEqual({
      label: "Check-in Kinds offered",
      value: "0",
    });
    expect(facts).toContainEqual({
      label: "Check-in Kind chosen",
      value: "None",
    });
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
      read_formed: true,
      read_said: true,
      check_in_kinds_offered: 2,
      check_in_kind: "A follow-up",
      pattern_used: true,
      pattern_offered: true,
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
    expect(facts.slice(-5)).toEqual([
      { label: "Read formed", value: "Yes" },
      { label: "Read said", value: "Yes" },
      { label: "Pattern", value: "Offered" },
      { label: "Check-in Kinds offered", value: "2" },
      { label: "Check-in Kind chosen", value: "A follow-up" },
    ]);
  });
});

describe("describePatternUse", () => {
  const shape = {
    need: "Be heard",
    lead_move: null,
    support_move: null,
    next_move: null,
    threads_reminded: 0,
    threads_led_with: 0,
    threads_woven_in: 0,
    threads_left_alone: 0,
    threads_held_back: 0,
    read_formed: true,
    read_said: false,
    check_in_kinds_offered: 0,
    check_in_kind: null,
  };

  it("says None when the Read used no Pattern", () => {
    expect(
      describePatternUse({
        ...shape,
        pattern_used: false,
        pattern_offered: false,
      }),
    ).toBe("None");
  });

  it("says a Pattern was used but not offered", () => {
    expect(
      describePatternUse({
        ...shape,
        pattern_used: true,
        pattern_offered: false,
      }),
    ).toBe("Used, not offered");
  });

  it("says a Pattern was offered", () => {
    expect(
      describePatternUse({
        ...shape,
        pattern_used: true,
        pattern_offered: true,
      }),
    ).toBe("Offered");
  });
});

describe("taggingShapeFacts", () => {
  it("names the tagging step and counts what was tagged and dropped", () => {
    expect(modelStepLabel("pattern_tagging")).toBe("Pattern tagging");
    expect(modelStepLabel("pattern_matching")).toBe("Pattern matching");
    expect(modelStepLabel("pattern_other_side")).toBe("Other side");
    expect(modelStepLabel("pattern_shared_check")).toBe("Pattern shared check");
    expect(modelStepLabel("prediction_given_check")).toBe(
      "Prediction given check",
    );
    expect(taggingShapeFacts({ tagged: 3, dropped: 1 })).toEqual([
      { label: "Observations tagged", value: "3" },
      { label: "Dropped by code", value: "1" },
    ]);
  });
});
