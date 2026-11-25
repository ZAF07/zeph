import type { ApiClient, UnmatchedEntry } from "@/lib/api-client";

/** The three Pattern Types of the design's catalog. */
const patternTypes = [
  { id: "ACH.WORTH.PERF", name: "Performance-contingent self-worth" },
  { id: "CONF.AVOID.BELONG", name: "Conflict avoidance to preserve belonging" },
  { id: "CTRL.UNCERT.PLAN", name: "Control-seeking under uncertainty" },
];

/** The unmatched entries drawn in `AdminUnmatchedPatterns`. */
const entries: UnmatchedEntry[] = [
  {
    id: "design-jokes",
    description: "Makes jokes when things get serious",
    user_count: 4,
    mark: "to_review",
    folded_into_pattern_type_id: null,
    dropped_before: false,
  },
  {
    id: "design-absorbed",
    description: "Lets everything else slip while absorbed in something",
    user_count: 2,
    mark: "to_review",
    folded_into_pattern_type_id: null,
    dropped_before: true,
  },
  {
    id: "design-backs-out",
    description: "Says yes to plans and backs out on the day",
    user_count: 1,
    mark: "to_review",
    folded_into_pattern_type_id: null,
    dropped_before: false,
  },
];

/** The Unmatched Patterns page's calls, answered as drawn. */
export const unmatchedPatternsFixtures: Partial<ApiClient> = {
  listUnmatchedEntries: async (mark) => ({
    entries: entries.filter((entry) => mark === null || entry.mark === mark),
    pattern_types: patternTypes,
  }),
};
