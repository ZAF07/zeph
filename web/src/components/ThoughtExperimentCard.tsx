"use client";

import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { FoldingCard } from "@/components/FoldingCard";
import { LeadingWordingConfirm } from "@/components/LeadingWordingConfirm";
import { ThoughtExperimentFields } from "@/components/ThoughtExperimentFields";
import type {
  PatternTypeChoice,
  ThoughtExperiment,
  ThoughtExperimentInput,
} from "@/lib/api-client";
import {
  isThoughtExperimentChanged,
  isThoughtExperimentComplete,
  pairTitle,
  thoughtExperimentInputOf,
} from "@/lib/thought-experiment-draft";
import { useCardAction } from "@/lib/use-card-action";
import { useLeadingWordingSave } from "@/lib/use-leading-wording-save";

/**
 * One Thought Experiment as a card of the card list. The folded row shows
 * the two Pattern Types it tells apart, the start of its wording, a
 * Starter or Off tag and how many times it was asked. Open, it has its
 * fields and the save bar with Archive in place of Remove. A save with
 * leading wording shows the phrases with Keep editing or Save anyway.
 *
 * @param props - `thoughtExperiment` is it as saved; `patternTypes` are
 *   the catalog's Pattern Types; `isOpen` and `onToggle` open and fold it;
 *   `onSave` saves, saving anyway or not, and rejects if the backend
 *   refuses; `onArchive` archives it and rejects if that fails.
 * @returns The card.
 */
export function ThoughtExperimentCard({
  thoughtExperiment,
  patternTypes,
  isOpen,
  onToggle,
  onSave,
  onArchive,
}: {
  thoughtExperiment: ThoughtExperiment;
  patternTypes: PatternTypeChoice[];
  isOpen: boolean;
  onToggle: () => void;
  onSave: (input: ThoughtExperimentInput, saveAnyway: boolean) => Promise<void>;
  onArchive: () => Promise<void>;
}) {
  const [draft, setDraft] = useState<ThoughtExperimentInput>(() =>
    thoughtExperimentInputOf(thoughtExperiment),
  );
  const [isConfirmingArchive, setIsConfirmingArchive] = useState(false);
  const action = useCardAction();
  const leading = useLeadingWordingSave(
    action,
    "Couldn’t save the Thought Experiment. Please try again.",
  );
  const isDirty = isThoughtExperimentChanged(draft, thoughtExperiment);

  function save(saveAnyway: boolean) {
    leading.save((anyway) => onSave(draft, anyway), saveAnyway);
  }

  let footer = (
    <CardSaveBar
      note="Changes apply from the next Conversation end. Past tries keep the words they were asked with."
      failedMessage={action.failedMessage}
      isDirty={isDirty}
      canSave={isDirty && isThoughtExperimentComplete(draft)}
      isBusy={action.isBusy}
      removeLabel="Archive"
      onRemove={() => setIsConfirmingArchive(true)}
      onDiscard={() => {
        setDraft(thoughtExperimentInputOf(thoughtExperiment));
        leading.dismiss();
        action.clearFailure();
      }}
      onSave={() => save(false)}
    />
  );
  if (leading.flags) {
    footer = (
      <LeadingWordingConfirm
        flags={leading.flags}
        isBusy={action.isBusy}
        onKeep={leading.dismiss}
        onSaveAnyway={() => save(true)}
      />
    );
  } else if (isConfirmingArchive) {
    footer = (
      <CardRemoveConfirm
        label="Archive this Thought Experiment?"
        title="Archive this Thought Experiment?"
        body="Zeph never asks it again, and a Curiosity waiting to ask it is closed. Past tries still show it. Archiving can’t be undone."
        confirmLabel="Archive"
        isBusy={action.isBusy}
        onKeep={() => setIsConfirmingArchive(false)}
        onConfirm={async () => {
          await action.run(
            onArchive,
            "Couldn’t archive the Thought Experiment. Please try again.",
          );
          setIsConfirmingArchive(false);
        }}
      />
    );
  }

  return (
    <FoldingCard
      title={pairTitle(thoughtExperiment)}
      summary={thoughtExperiment.wording}
      tags={
        <>
          {thoughtExperiment.starter ? <CardTag>Starter</CardTag> : null}
          {thoughtExperiment.on ? null : <CardTag>Off</CardTag>}
        </>
      }
      meta={
        <CardCount
          count={thoughtExperiment.asked_count}
          words={
            thoughtExperiment.asked_count === 1 ? "time asked" : "times asked"
          }
        />
      }
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
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
      {footer}
    </FoldingCard>
  );
}
