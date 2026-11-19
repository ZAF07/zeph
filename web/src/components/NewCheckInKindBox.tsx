"use client";

import { useState } from "react";

import { CardTextField } from "@/components/CardTextField";
import { NewCardBox } from "@/components/NewCardBox";
import type { CheckInKindInput } from "@/lib/api-client";
import { useCardAction } from "@/lib/use-card-action";

/**
 * The box for adding a Check-in Kind, shown above the list.
 *
 * @param props - `onAdd` adds the Kind and rejects if the backend refuses;
 *   `onCancel` closes the box.
 * @returns The box.
 */
export function NewCheckInKindBox({
  onAdd,
  onCancel,
}: {
  onAdd: (input: CheckInKindInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const action = useCardAction();

  return (
    <NewCardBox
      title="New Check-in Kind"
      failedMessage={action.failedMessage}
      canAdd={name.trim() !== "" && description.trim() !== ""}
      isBusy={action.isBusy}
      onCancel={onCancel}
      onAdd={() =>
        void action.run(
          () => onAdd({ name, description }),
          "Couldn’t save the Check-in Kind. Please try again.",
        )
      }
    >
      <CardTextField
        label="Name"
        placeholder="e.g. A casual hello"
        value={name}
        onChange={setName}
      />
      <CardTextField
        label="Description"
        value={description}
        multiline
        onChange={setDescription}
      />
    </NewCardBox>
  );
}
