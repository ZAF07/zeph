import { diffWordsWithSpace } from "diff";

import { countWords } from "@/lib/text-stats";

/** One stretch of a comparison between saved and edited text. */
export type TextChangePart =
  | { kind: "same" | "added" | "removed"; text: string }
  | { kind: "skipped"; characters: number };

/** How edited text differs from the saved text. */
export type TextComparison = {
  parts: TextChangePart[];
  addedWords: number;
  removedWords: number;
  hasChanges: boolean;
};

const longestUnchanged = 240;
const unchangedContext = 80;

/**
 * Shortens a long unchanged stretch to a little text either side of a gap.
 *
 * @param text - The unchanged text.
 * @param isFirst - Whether it starts the text, so nothing comes before it.
 * @param isLast - Whether it ends the text, so nothing comes after it.
 * @returns The parts to show for it.
 */
function shortenUnchanged(
  text: string,
  isFirst: boolean,
  isLast: boolean,
): TextChangePart[] {
  if (text.length <= longestUnchanged) {
    return [{ kind: "same", text }];
  }
  const before = isFirst ? "" : text.slice(0, unchangedContext);
  const after = isLast ? "" : text.slice(-unchangedContext);
  const parts: TextChangePart[] = [];
  if (before) {
    parts.push({ kind: "same", text: before });
  }
  parts.push({
    kind: "skipped",
    characters: text.length - before.length - after.length,
  });
  if (after) {
    parts.push({ kind: "same", text: after });
  }
  return parts;
}

/**
 * Compares saved text with an edited version word by word, shortening long
 * stretches that didn't change.
 *
 * @param saved - The saved text.
 * @param edited - The edited text.
 * @returns The changed and unchanged stretches, in order, and how many
 *   words were added and removed.
 */
export function compareTexts(saved: string, edited: string): TextComparison {
  const changes = diffWordsWithSpace(saved, edited);
  let addedWords = 0;
  let removedWords = 0;
  const parts = changes.flatMap((change, index): TextChangePart[] => {
    if (change.added) {
      addedWords += countWords(change.value);
      return [{ kind: "added", text: change.value }];
    }
    if (change.removed) {
      removedWords += countWords(change.value);
      return [{ kind: "removed", text: change.value }];
    }
    return shortenUnchanged(
      change.value,
      index === 0,
      index === changes.length - 1,
    );
  });
  return {
    parts,
    addedWords,
    removedWords,
    hasChanges: changes.some((change) => change.added || change.removed),
  };
}
