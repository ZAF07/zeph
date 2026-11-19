"use client";

import { useState } from "react";

import { CardMoveButtons } from "@/components/CardMoveButtons";
import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { FoldingCard } from "@/components/FoldingCard";
import { MoveFields } from "@/components/MoveFields";
import type {
  FeatureSwitch,
  Move,
  MoveDirection,
  MoveInput,
} from "@/lib/api-client";
import { isMoveChanged, isMoveComplete, moveInputOf } from "@/lib/move-draft";
import { useCardAction } from "@/lib/use-card-action";

/**
 * One Move as a card of the card list. The folded row shows its name and
 * the start of "when it fits". Open, it has the Move's fields and the save
 * bar with Move up and down and Remove.
 *
 * @param props - `move` is the Move as saved; `features` are the Features
 *   it can need; `isOpen` and `onToggle` open and fold it; `onSave` saves
 *   and rejects if the backend refuses; `onRemove` removes it; `onMove`,
 *   `canMoveUp`, `canMoveDown` and `isMoving` reorder it.
 * @returns The card.
 */
export function MoveCard({
  move,
  features,
  isOpen,
  onToggle,
  onSave,
  onRemove,
  onMove,
  canMoveUp,
  canMoveDown,
  isMoving,
}: {
  move: Move;
  features: FeatureSwitch[];
  isOpen: boolean;
  onToggle: () => void;
  onSave: (input: MoveInput) => Promise<void>;
  onRemove: () => Promise<void>;
  onMove: (direction: MoveDirection) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isMoving: boolean;
}) {
  const [draft, setDraft] = useState<MoveInput>(move);
  const [isConfirmingRemove, setIsConfirmingRemove] = useState(false);
  const action = useCardAction();
  const isDirty = isMoveChanged(draft, move);

  return (
    <FoldingCard
      title={move.name}
      summary={move.when_it_fits}
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <MoveFields
        value={draft}
        features={features}
        onChange={(next) => {
          setDraft(next);
          action.clearFailure();
        }}
      />
      {isConfirmingRemove ? (
        <CardRemoveConfirm
          label="Remove this Move?"
          title={`Remove “${move.name}”?`}
          body="Zeph stops making this Move."
          isBusy={action.isBusy}
          onKeep={() => setIsConfirmingRemove(false)}
          onConfirm={async () => {
            await action.run(
              onRemove,
              "Couldn’t remove the Move. Please try again.",
            );
            setIsConfirmingRemove(false);
          }}
        />
      ) : (
        <CardSaveBar
          note="Changes apply to the next message after saving."
          leading={
            <CardMoveButtons
              name={move.name}
              canMoveUp={canMoveUp}
              canMoveDown={canMoveDown}
              isMoving={isMoving}
              onMove={onMove}
            />
          }
          failedMessage={action.failedMessage}
          isDirty={isDirty}
          canSave={isDirty && isMoveComplete(draft)}
          isBusy={action.isBusy}
          onRemove={() => setIsConfirmingRemove(true)}
          onDiscard={() => {
            setDraft(move);
            action.clearFailure();
          }}
          onSave={() =>
            void action.run(
              () => onSave(moveInputOf(draft)),
              "Couldn’t save the Move. Please try again.",
            )
          }
        />
      )}
    </FoldingCard>
  );
}
