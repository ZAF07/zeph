"use client";

import { useState } from "react";

import { MemoryCategoryFields } from "@/components/MemoryCategoryFields";
import { NewCardBox } from "@/components/NewCardBox";
import type { MemoryCategoryInput } from "@/lib/api-client";
import { useCardAction } from "@/lib/use-card-action";

/**
 * The box for adding a Memory Category, shown above the list.
 *
 * @param props - `onAdd` adds the category and rejects if the backend
 *   refuses; `onCancel` closes the box.
 * @returns The box.
 */
export function NewMemoryCategoryBox({
  onAdd,
  onCancel,
}: {
  onAdd: (input: MemoryCategoryInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const action = useCardAction();

  return (
    <NewCardBox
      title="New category"
      failedMessage={action.failedMessage}
      canAdd={name.trim() !== "" && description.trim() !== ""}
      isBusy={action.isBusy}
      onCancel={onCancel}
      onAdd={() =>
        void action.run(
          () => onAdd({ name, description, always_include: false }),
          "Couldn’t save the category. Please try again.",
        )
      }
    >
      <MemoryCategoryFields
        name={name}
        description={description}
        onNameChange={setName}
        onDescriptionChange={setDescription}
      />
    </NewCardBox>
  );
}
