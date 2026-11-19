"use client";

import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { CardTextField } from "@/components/CardTextField";
import { FoldingCard } from "@/components/FoldingCard";
import type { CheckInKindInput, CheckInKindOverview } from "@/lib/api-client";
import { useCardAction } from "@/lib/use-card-action";

/**
 * One Check-in Kind as a card of the card list. The folded row shows its
 * name, the start of its description, a tag if it sends a Shared Photo or
 * asks a Curiosity, and how often it was sent. Open, it has the name and
 * description fields and the save bar with Remove.
 *
 * @param props - `kind` is the Kind as saved; `isOpen` and `onToggle` open
 *   and fold it; `onSave` saves and rejects if the backend refuses;
 *   `onRemove` removes it.
 * @returns The card.
 */
export function CheckInKindCard({
  kind,
  isOpen,
  onToggle,
  onSave,
  onRemove,
}: {
  kind: CheckInKindOverview;
  isOpen: boolean;
  onToggle: () => void;
  onSave: (input: CheckInKindInput) => Promise<void>;
  onRemove: () => Promise<void>;
}) {
  const [name, setName] = useState(kind.name);
  const [description, setDescription] = useState(kind.description);
  const [isConfirmingRemove, setIsConfirmingRemove] = useState(false);
  const action = useCardAction();

  const isDirty = name !== kind.name || description !== kind.description;
  const isComplete = name.trim() !== "" && description.trim() !== "";

  function edit(setValue: (value: string) => void) {
    return (value: string) => {
      setValue(value);
      action.clearFailure();
    };
  }

  return (
    <FoldingCard
      title={kind.name}
      summary={kind.description}
      tags={
        <>
          {kind.sends_shared_photo ? (
            <CardTag locked>Sends a Shared Photo</CardTag>
          ) : null}
          {kind.raises_curiosity ? (
            <CardTag locked>Asks a Curiosity</CardTag>
          ) : null}
        </>
      }
      meta={
        <CardCount count={kind.sent_last_30_days} words="sent in 30 days" />
      }
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <CardTextField
        label="Name"
        hint="Users see this name, read-only, on their Check-ins page."
        value={name}
        onChange={edit(setName)}
      />
      <CardTextField
        label="Description"
        hint="The Check-ins service reads this to choose a kind, or to skip. Write when it fits, not what to say."
        value={description}
        multiline
        onChange={edit(setDescription)}
      />
      {isConfirmingRemove ? (
        <CardRemoveConfirm
          label="Remove this kind?"
          title={`Remove “${kind.name}”?`}
          body="Zeph stops sending this kind. Past check-ins of this kind stay in the log."
          isBusy={action.isBusy}
          onKeep={() => setIsConfirmingRemove(false)}
          onConfirm={async () => {
            await action.run(
              onRemove,
              "Couldn’t remove the Check-in Kind. Please try again.",
            );
            setIsConfirmingRemove(false);
          }}
        />
      ) : (
        <CardSaveBar
          note="Changes apply to the next check-in after saving."
          failedMessage={action.failedMessage}
          isDirty={isDirty}
          canSave={isDirty && isComplete}
          isBusy={action.isBusy}
          onRemove={() => setIsConfirmingRemove(true)}
          onDiscard={() => {
            setName(kind.name);
            setDescription(kind.description);
            action.clearFailure();
          }}
          onSave={() =>
            void action.run(
              () => onSave({ name, description }),
              "Couldn’t save the Check-in Kind. Please try again.",
            )
          }
        />
      )}
    </FoldingCard>
  );
}
