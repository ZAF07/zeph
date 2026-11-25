"use client";

import { useId, useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { FieldRow } from "@/components/FieldRow";
import { FieldSelect } from "@/components/FieldSelect";
import { FoldingCard } from "@/components/FoldingCard";
import type { PatternTypeChoice, UnmatchedEntry } from "@/lib/api-client";
import { patternTypeOptions } from "@/lib/thought-experiment-draft";
import {
  MARK_OPTIONS,
  type UnmatchedMarkDraft,
  isMarkChanged,
  isMarkComplete,
  markDraftOf,
  markOf,
  markWords,
  userWords,
} from "@/lib/unmatched-entry-draft";
import { useCardAction } from "@/lib/use-card-action";

/**
 * One unmatched entry as a card of the card list. The folded row shows its
 * general description, its mark in words, a tag if it came back after
 * being dropped, and how many Users it appears for. Open, an Admin sets
 * its mark, and the Pattern Type when it is folded into one.
 *
 * @param props - `entry` is it as saved; `patternTypes` are the catalog's
 *   Pattern Types; `isOpen` and `onToggle` open and fold it; `onSave`
 *   saves the mark and rejects if the backend refuses.
 * @returns The card.
 */
export function UnmatchedEntryCard({
  entry,
  patternTypes,
  isOpen,
  onToggle,
  onSave,
}: {
  entry: UnmatchedEntry;
  patternTypes: PatternTypeChoice[];
  isOpen: boolean;
  onToggle: () => void;
  onSave: (draft: UnmatchedMarkDraft) => Promise<void>;
}) {
  const fieldId = useId();
  const [draft, setDraft] = useState<UnmatchedMarkDraft>(() =>
    markDraftOf(entry),
  );
  const action = useCardAction();
  const isDirty = isMarkChanged(draft, entry);

  function change(next: UnmatchedMarkDraft) {
    setDraft(next);
    action.clearFailure();
  }

  return (
    <FoldingCard
      title={entry.description}
      summary={markWords(entry)}
      tags={
        entry.dropped_before ? (
          <CardTag tone="orange">Back after a drop</CardTag>
        ) : null
      }
      meta={
        <CardCount
          count={entry.user_count}
          words={userWords(entry.user_count)}
        />
      }
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <ul className="m-0 list-none p-0">
        <FieldRow
          title="Mark"
          caption="What you decided about it. A mark changes nothing for Users: writing a Pattern Type into the catalog stays manual."
          htmlFor={`${fieldId}-mark`}
        >
          <FieldSelect
            id={`${fieldId}-mark`}
            value={draft.mark}
            options={MARK_OPTIONS}
            onChange={(chosen) => change({ ...draft, mark: markOf(chosen) })}
          />
        </FieldRow>
        {draft.mark === "folded" ? (
          <FieldRow
            title="Folded into"
            caption="The Pattern Type that covers it. Once its signs are in the catalog, run the matching command for that Pattern Type."
            htmlFor={`${fieldId}-pattern-type`}
          >
            <FieldSelect
              id={`${fieldId}-pattern-type`}
              value={draft.patternTypeId}
              options={patternTypeOptions(patternTypes, draft.patternTypeId)}
              onChange={(chosen) => change({ ...draft, patternTypeId: chosen })}
            />
          </FieldRow>
        ) : null}
      </ul>
      <CardSaveBar
        note="A dropped entry comes back to review only if it appears for more Users."
        failedMessage={action.failedMessage}
        isDirty={isDirty}
        canSave={isDirty && isMarkComplete(draft)}
        isBusy={action.isBusy}
        onDiscard={() => change(markDraftOf(entry))}
        onSave={() =>
          void action.run(
            () => onSave(draft),
            "Couldn’t save the mark. Please try again.",
          )
        }
      />
    </FoldingCard>
  );
}
