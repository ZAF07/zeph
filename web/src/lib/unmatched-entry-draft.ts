import type { UnmatchedEntry, UnmatchedMark } from "@/lib/api-client";

/** Which entries the page lists: every one, or those with one mark. */
export type UnmatchedFilter = UnmatchedMark | "all";

/** An entry's mark as edited: the mark, and the Pattern Type when folded. */
export type UnmatchedMarkDraft = {
  mark: UnmatchedMark;
  patternTypeId: string;
};

/** The marks to choose from, in the order an Admin meets them. */
export const MARK_OPTIONS: { value: UnmatchedMark; label: string }[] = [
  { value: "to_review", label: "To review" },
  { value: "new_pattern_type", label: "New Pattern Type" },
  { value: "folded", label: "Folded into a Pattern Type" },
  { value: "dropped", label: "Dropped" },
];

/** The filter pills, the entries still to review first. */
export const FILTER_OPTIONS: { id: UnmatchedFilter; label: string }[] = [
  { id: "to_review", label: "To review" },
  { id: "new_pattern_type", label: "New Pattern Type" },
  { id: "folded", label: "Folded" },
  { id: "dropped", label: "Dropped" },
  { id: "all", label: "All" },
];

/**
 * Reads a chosen mark from a select's value.
 *
 * @param value - The select's value.
 * @returns The mark; "to_review" if the value is not a mark.
 */
export function markOf(value: string): UnmatchedMark {
  const option = MARK_OPTIONS.find((choice) => choice.value === value);
  return option ? option.value : "to_review";
}

/**
 * Takes the mark an Admin can change from a saved entry.
 *
 * @param entry - The entry as saved.
 * @returns Its mark and the Pattern Type it is folded into, "" for none.
 */
export function markDraftOf(entry: UnmatchedEntry): UnmatchedMarkDraft {
  return {
    mark: entry.mark,
    patternTypeId: entry.folded_into_pattern_type_id ?? "",
  };
}

/**
 * Says whether a draft differs from the saved entry.
 *
 * @param draft - The mark as edited.
 * @param entry - The entry as saved.
 * @returns True when the mark changed, or the Pattern Type of a folded one.
 */
export function isMarkChanged(
  draft: UnmatchedMarkDraft,
  entry: UnmatchedEntry,
): boolean {
  const saved = markDraftOf(entry);
  return (
    draft.mark !== saved.mark ||
    (draft.mark === "folded" && draft.patternTypeId !== saved.patternTypeId)
  );
}

/**
 * Says whether a draft can be saved: a folded one names its Pattern Type.
 *
 * @param draft - The mark as edited.
 * @returns True when it is complete.
 */
export function isMarkComplete(draft: UnmatchedMarkDraft): boolean {
  return draft.mark !== "folded" || draft.patternTypeId !== "";
}

/**
 * Words for an entry's mark, for its folded row.
 *
 * @param entry - The entry as saved.
 * @returns E.g. "To review" or "Folded into CONF.AVOID.BELONG".
 */
export function markWords(entry: UnmatchedEntry): string {
  if (entry.mark === "folded") {
    return `Folded into ${entry.folded_into_pattern_type_id ?? "a Pattern Type"}`;
  }
  if (entry.mark === "new_pattern_type") {
    return "To become a new Pattern Type";
  }
  return entry.mark === "dropped" ? "Dropped" : "To review";
}

/**
 * Words for how many Users an entry appears for.
 *
 * @param count - How many Users.
 * @returns "User" for one, "Users" otherwise.
 */
export function userWords(count: number): string {
  return count === 1 ? "User" : "Users";
}
