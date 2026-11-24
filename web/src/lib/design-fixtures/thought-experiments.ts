import type { ApiClient, ThoughtExperiment } from "@/lib/api-client";

/** The three Pattern Types of the design's catalog. */
const patternTypes = [
  { id: "ACH.WORTH.PERF", name: "Performance-contingent self-worth" },
  { id: "CONF.AVOID.BELONG", name: "Conflict avoidance to preserve belonging" },
  { id: "CTRL.UNCERT.PLAN", name: "Control-seeking under uncertainty" },
];

/** The Thought Experiments drawn in `AdminThoughtExperiments`. */
const thoughtExperiments: ThoughtExperiment[] = [
  {
    id: "design-team-plan",
    wording:
      "Your team lead, who you get on well with, shares a plan in a meeting and you can see a real problem with it. Nobody else has spoken up. What do you do, and what's on your mind as you decide?",
    pattern_type_id: "CONF.AVOID.BELONG",
    other_pattern_type_id: "ACH.WORTH.PERF",
    sensitivity: "low",
    starter: true,
    on: true,
    archived_at: null,
    asked_count: 12,
  },
  {
    id: "design-friend-feedback",
    wording:
      "A close friend reads something you wrote and says, kindly, that one part doesn't work. Afterwards, what stays with you more: that the part wasn't good enough, or that things might feel a little awkward between you? And what do you say back to them?",
    pattern_type_id: "CONF.AVOID.BELONG",
    other_pattern_type_id: "ACH.WORTH.PERF",
    sensitivity: "low",
    starter: false,
    on: true,
    archived_at: null,
    asked_count: 7,
  },
  {
    id: "design-friend-or-shop",
    wording:
      "Picture two times you disagree with a decision: once with a close friend, once with a shop that got your order wrong. How it will turn out is just as unclear both times. In which one is it harder for you to speak up, and why?",
    pattern_type_id: "CONF.AVOID.BELONG",
    other_pattern_type_id: "CTRL.UNCERT.PLAN",
    sensitivity: "low",
    starter: false,
    on: false,
    archived_at: null,
    asked_count: 0,
  },
  {
    id: "design-credit-taken",
    wording:
      "A colleague takes the credit for your idea in a meeting. What do you do next?",
    pattern_type_id: "ACH.WORTH.PERF",
    other_pattern_type_id: "CTRL.UNCERT.PLAN",
    sensitivity: "medium",
    starter: false,
    on: false,
    archived_at: "2026-11-20T10:00:00Z",
    asked_count: 3,
  },
];

/** The Thought Experiments page's calls, answered as drawn. */
export const thoughtExperimentsFixtures: Partial<ApiClient> = {
  listThoughtExperiments: async () => ({
    thought_experiments: thoughtExperiments,
    pattern_types: patternTypes,
  }),
};
