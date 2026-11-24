import type { PatternType } from "@/lib/api-client";

/** A draft Pattern Type with one of everything, for tests. */
export const patternType: PatternType = {
  id: "CONF.AVOID.BELONG",
  version: "0.2.0",
  area: "conflict",
  name: "Conflict avoidance to preserve belonging",
  definition: "The person dilutes their own position to keep the peace.",
  if_situation: "Disagreement with a valued other",
  then_behaviour: "Withholds or softens own view",
  function: "To protect belonging",
  frameworks: ["Young's subjugation schema", "Anxious attachment (ECR-R)"],
  signs: [
    {
      id: "I1",
      text: "Apologises or hedges before stating a need",
      strength: "moderate",
      part: "behaviour",
    },
  ],
  signs_against: [
    {
      id: "D1",
      text: "States disagreement directly with close others",
      strength: "strong",
      part: "inside",
    },
  ],
  look_alikes: [
    {
      pattern_type_id: "ACH.WORTH.PERF",
      name: "Performance-contingent self-worth",
      tells_apart: "Avoids conflict because criticism means failure",
    },
    {
      pattern_type_id: null,
      name: "Plain politeness",
      tells_apart: "Says it later without distress",
    },
  ],
  anyone_would: "Low-stakes avoidance with strangers",
  exclusions: [
    { text: "Grief", evidence: "ignored" },
    { text: "Job loss in the last month", evidence: "counted_not_shared" },
  ],
  approved_wording: "You seem to protect closeness.",
  prediction_wording: "Next time {person} asks, notice what you say.",
  numbers: { situations_needed: 3, base_rate: 0.2 },
  status: "draft",
  approved_by: null,
  approved_on: null,
  loaded_at: "2026-11-24T09:00:00Z",
  other_versions: ["0.1.0"],
};
