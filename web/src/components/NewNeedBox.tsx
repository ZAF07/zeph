"use client";

import { useState } from "react";

import { NeedFields } from "@/components/NeedFields";
import { NewCardBox } from "@/components/NewCardBox";
import type { Move, NeedInput } from "@/lib/api-client";
import { defaultCuriosityTreatment } from "@/lib/curiosity-treatment";
import { isNeedComplete } from "@/lib/need-draft";
import { useCardAction } from "@/lib/use-card-action";

const emptyNeed: NeedInput = {
  name: "",
  when_it_fits: "",
  how_to_reply: "",
  ruled_out_move_ids: [],
  curiosities: defaultCuriosityTreatment,
};

/**
 * The box for adding a Need, shown above the list.
 *
 * @param props - `moves` are every Move, to rule out; `onAdd` adds the
 *   Need and rejects if the backend refuses; `onCancel` closes the box.
 * @returns The box.
 */
export function NewNeedBox({
  moves,
  onAdd,
  onCancel,
}: {
  moves: Move[];
  onAdd: (input: NeedInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState(emptyNeed);
  const action = useCardAction();

  return (
    <NewCardBox
      title="New Need"
      failedMessage={action.failedMessage}
      canAdd={isNeedComplete(draft)}
      isBusy={action.isBusy}
      onCancel={onCancel}
      onAdd={() =>
        void action.run(
          () => onAdd(draft),
          "Couldn’t save the Need. Please try again.",
        )
      }
    >
      <NeedFields
        value={draft}
        moves={moves}
        idPrefix="new-need"
        onChange={setDraft}
      />
    </NewCardBox>
  );
}
