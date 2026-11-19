"use client";

import { useState } from "react";

import { CardMoveButtons } from "@/components/CardMoveButtons";
import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { FoldingCard } from "@/components/FoldingCard";
import { NeedFields } from "@/components/NeedFields";
import type { Move, MoveDirection, Need, NeedInput } from "@/lib/api-client";
import { isNeedChanged, isNeedComplete, needInputOf } from "@/lib/need-draft";
import { useCardAction } from "@/lib/use-card-action";

/**
 * One Need as a card of the card list. The folded row shows its name, the
 * start of "when it fits" and a tag on the fallback Need. Open, it has the
 * Need's fields and the save bar with Move up and down and Remove. The
 * fallback Need has no Remove, and its bar says so.
 *
 * @param props - `need` is the Need as saved; `moves` are every Move;
 *   `isOpen` and `onToggle` open and fold it; `onSave` saves and rejects if
 *   the backend refuses; `onRemove` removes it; `onMove`, `canMoveUp`,
 *   `canMoveDown` and `isMoving` reorder it.
 * @returns The card.
 */
export function NeedCard({
  need,
  moves,
  isOpen,
  onToggle,
  onSave,
  onRemove,
  onMove,
  canMoveUp,
  canMoveDown,
  isMoving,
}: {
  need: Need;
  moves: Move[];
  isOpen: boolean;
  onToggle: () => void;
  onSave: (input: NeedInput) => Promise<void>;
  onRemove: () => Promise<void>;
  onMove: (direction: MoveDirection) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isMoving: boolean;
}) {
  const [draft, setDraft] = useState<NeedInput>(need);
  const [isConfirmingRemove, setIsConfirmingRemove] = useState(false);
  const action = useCardAction();
  const isDirty = isNeedChanged(draft, need);

  return (
    <FoldingCard
      title={need.name}
      summary={need.when_it_fits}
      tags={need.is_fallback ? <CardTag locked>Fallback</CardTag> : null}
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <NeedFields
        value={draft}
        moves={moves}
        onChange={(next) => {
          setDraft(next);
          action.clearFailure();
        }}
      />
      {isConfirmingRemove ? (
        <CardRemoveConfirm
          label="Remove this Need?"
          title={`Remove “${need.name}”?`}
          body="Zeph stops picking this Need."
          isBusy={action.isBusy}
          onKeep={() => setIsConfirmingRemove(false)}
          onConfirm={async () => {
            await action.run(
              onRemove,
              "Couldn’t remove the Need. Please try again.",
            );
            setIsConfirmingRemove(false);
          }}
        />
      ) : (
        <CardSaveBar
          note={
            need.is_fallback
              ? "Fallback · can’t be deleted"
              : "Changes apply to the next message after saving."
          }
          leading={
            <CardMoveButtons
              name={need.name}
              canMoveUp={canMoveUp}
              canMoveDown={canMoveDown}
              isMoving={isMoving}
              onMove={onMove}
            />
          }
          failedMessage={action.failedMessage}
          isDirty={isDirty}
          canSave={isDirty && isNeedComplete(draft)}
          isBusy={action.isBusy}
          onRemove={
            need.is_fallback ? undefined : () => setIsConfirmingRemove(true)
          }
          onDiscard={() => {
            setDraft(need);
            action.clearFailure();
          }}
          onSave={() =>
            void action.run(
              () => onSave(needInputOf(draft)),
              "Couldn’t save the Need. Please try again.",
            )
          }
        />
      )}
    </FoldingCard>
  );
}
