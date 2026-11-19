"use client";

import { useState } from "react";

import { MoveFields } from "@/components/MoveFields";
import { NewCardBox } from "@/components/NewCardBox";
import type { FeatureSwitch, MoveInput } from "@/lib/api-client";
import { isMoveComplete } from "@/lib/move-draft";
import { useCardAction } from "@/lib/use-card-action";

const emptyMove: MoveInput = {
  name: "",
  when_it_fits: "",
  how_to_do_it: "",
  needed_feature: null,
  asks_a_question: false,
};

/**
 * The box for adding a Move, shown above the list.
 *
 * @param props - `features` are the Features it can need; `onAdd` adds the
 *   Move and rejects if the backend refuses; `onCancel` closes the box.
 * @returns The box.
 */
export function NewMoveBox({
  features,
  onAdd,
  onCancel,
}: {
  features: FeatureSwitch[];
  onAdd: (input: MoveInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState(emptyMove);
  const action = useCardAction();

  return (
    <NewCardBox
      title="New Move"
      failedMessage={action.failedMessage}
      canAdd={isMoveComplete(draft)}
      isBusy={action.isBusy}
      onCancel={onCancel}
      onAdd={() =>
        void action.run(
          () => onAdd(draft),
          "Couldn’t save the Move. Please try again.",
        )
      }
    >
      <MoveFields value={draft} features={features} onChange={setDraft} />
    </NewCardBox>
  );
}
