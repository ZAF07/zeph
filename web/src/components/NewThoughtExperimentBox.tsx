"use client";

import { useState } from "react";

import { LeadingWordingConfirm } from "@/components/LeadingWordingConfirm";
import { NewCardBox } from "@/components/NewCardBox";
import { ThoughtExperimentFields } from "@/components/ThoughtExperimentFields";
import type {
  PatternTypeChoice,
  ThoughtExperimentInput,
} from "@/lib/api-client";
import {
  EMPTY_THOUGHT_EXPERIMENT,
  SAVE_FAILED_TEXT,
  isThoughtExperimentComplete,
} from "@/lib/thought-experiment-draft";
import { useCardAction } from "@/lib/use-card-action";
import { useLeadingWordingSave } from "@/lib/use-leading-wording-save";

/**
 * The box for adding a Thought Experiment, shown above the list. Adding one
 * with leading wording shows the phrases with Keep editing or Save anyway.
 *
 * @param props - `patternTypes` are the catalog's Pattern Types; `onAdd`
 *   adds it, saving anyway or not, and rejects if the backend refuses;
 *   `onCancel` closes the box.
 * @returns The box.
 */
export function NewThoughtExperimentBox({
  patternTypes,
  onAdd,
  onCancel,
}: {
  patternTypes: PatternTypeChoice[];
  onAdd: (input: ThoughtExperimentInput, saveAnyway: boolean) => Promise<void>;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<ThoughtExperimentInput>(
    EMPTY_THOUGHT_EXPERIMENT,
  );
  const action = useCardAction();
  const leading = useLeadingWordingSave(action, SAVE_FAILED_TEXT);

  return (
    <NewCardBox
      title="New Thought Experiment"
      failedMessage={action.failedMessage}
      canAdd={isThoughtExperimentComplete(draft) && !leading.flags}
      isBusy={action.isBusy}
      onCancel={onCancel}
      onAdd={() => leading.save((anyway) => onAdd(draft, anyway), false)}
    >
      <ThoughtExperimentFields
        value={draft}
        patternTypes={patternTypes}
        onChange={(next) => {
          setDraft(next);
          leading.dismiss();
          action.clearFailure();
        }}
      />
      {leading.flags ? (
        <LeadingWordingConfirm
          flags={leading.flags}
          isBusy={action.isBusy}
          onKeep={leading.dismiss}
          onSaveAnyway={() =>
            leading.save((anyway) => onAdd(draft, anyway), true)
          }
        />
      ) : null}
    </NewCardBox>
  );
}
