import type {
  MissedPattern,
  PatternState,
  ReadyPattern,
} from "@/lib/api-client";

const stateLabels: Record<PatternState, string> = {
  noticed: "Noticed",
  suspected: "Suspected",
  ready: "Ready",
  shared: "Shared",
  confirmed: "Confirmed",
  contested: "Contested",
  closed: "Closed",
  unmatched: "Unmatched",
};

const readyCheckLabels: Record<string, string> = {
  situations: "Too few situations",
  conversations: "Too few Conversations",
  clear: "Too little clear evidence",
  score: "Score under the bar",
  counter_test: "No answered counter-test",
  situational: "Rests on what anyone would do",
  quotes: "A quote isn’t word for word",
  other_side: "The other side explains it better",
  safe: "Not safe to share",
  allowed: "Pattern Type not approved",
};

/**
 * Names a Pattern by its Pattern Type's ID and name.
 *
 * @param pattern - The Pattern.
 * @returns E.g. "CONF.AVOID.BELONG · Softening disagreement to protect
 *   belonging"; the ID alone when the catalog gave no name.
 */
export function describePattern(pattern: ReadyPattern | MissedPattern): string {
  return [pattern.pattern_type, pattern.name].filter(Boolean).join(" · ");
}

/**
 * Says where a Pattern stands at the end of the case.
 *
 * @param state - Its state; null when the User has no such Pattern.
 * @returns E.g. "Suspected"; "Never noticed" with no Pattern.
 */
export function describeState(state: PatternState | null): string {
  return state === null ? "Never noticed" : stateLabels[state];
}

/**
 * Says which ready check last stopped a Pattern.
 *
 * @param blockedBy - The check; null when none did.
 * @returns E.g. "Too few situations"; "Nothing yet" with no check.
 */
export function describeBlockedBy(blockedBy: string | null): string {
  return blockedBy === null
    ? "Nothing yet"
    : (readyCheckLabels[blockedBy] ?? blockedBy);
}
