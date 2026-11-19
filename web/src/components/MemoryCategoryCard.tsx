"use client";

import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { FieldRow } from "@/components/FieldRow";
import { FoldingCard } from "@/components/FoldingCard";
import { MemoryCategoryFields } from "@/components/MemoryCategoryFields";
import { Switch } from "@/components/Switch";
import type {
  MemoryCategoryInput,
  MemoryCategoryOverview,
} from "@/lib/api-client";
import { useCardAction } from "@/lib/use-card-action";

/**
 * One active Memory Category as a card of the card list. The folded row
 * shows its name, the start of its description, an "Always included" tag
 * and how many Memory Items it has. Open, it has the name and description,
 * the "Always include" switch (saved the moment it is flipped) and the save
 * bar with Archive in place of Remove. There is no delete.
 *
 * @param props - `category` is the category as saved; `isOpen` and
 *   `onToggle` open and fold it; `onSave` saves the name and description
 *   and rejects if the backend refuses; `onAlwaysIncludeChange` saves the
 *   switch; `onArchive` archives it; `isChanging` turns those two off while
 *   one saves.
 * @returns The card.
 */
export function MemoryCategoryCard({
  category,
  isOpen,
  onToggle,
  onSave,
  onAlwaysIncludeChange,
  onArchive,
  isChanging,
}: {
  category: MemoryCategoryOverview;
  isOpen: boolean;
  onToggle: () => void;
  onSave: (input: MemoryCategoryInput) => Promise<void>;
  onAlwaysIncludeChange: (alwaysInclude: boolean) => void;
  onArchive: () => void;
  isChanging: boolean;
}) {
  const [name, setName] = useState(category.name);
  const [description, setDescription] = useState(category.description);
  const [isConfirmingArchive, setIsConfirmingArchive] = useState(false);
  const action = useCardAction();

  const isDirty =
    name !== category.name || description !== category.description;
  const isComplete = name.trim() !== "" && description.trim() !== "";

  return (
    <FoldingCard
      title={category.name}
      summary={category.description}
      tags={category.always_include ? <CardTag>Always included</CardTag> : null}
      meta={
        <CardCount
          count={category.item_count}
          words={category.item_count === 1 ? "item" : "items"}
        />
      }
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <MemoryCategoryFields
        name={name}
        description={description}
        onNameChange={(next) => {
          setName(next);
          action.clearFailure();
        }}
        onDescriptionChange={(next) => {
          setDescription(next);
          action.clearFailure();
        }}
      />
      <ul className="m-0 list-none p-0">
        <FieldRow
          title="Always include"
          caption="Sends every memory in this category to Zeph on each reply, not just the most relevant ones. Use sparingly. Saved as soon as it is switched."
        >
          <Switch
            label={`Always include ${category.name}`}
            checked={category.always_include}
            disabled={isChanging}
            onChange={onAlwaysIncludeChange}
          />
        </FieldRow>
      </ul>
      {isConfirmingArchive ? (
        <CardRemoveConfirm
          label="Archive this category?"
          title={`Archive “${category.name}”?`}
          body="Zeph stops saving new memories there. Users still see and can delete the ones they have."
          confirmLabel="Archive"
          isBusy={isChanging}
          onKeep={() => setIsConfirmingArchive(false)}
          onConfirm={() => {
            setIsConfirmingArchive(false);
            onArchive();
          }}
        />
      ) : (
        <CardSaveBar
          note="Changes apply to the next message after saving."
          failedMessage={action.failedMessage}
          isDirty={isDirty}
          canSave={isDirty && isComplete}
          isBusy={action.isBusy}
          removeLabel="Archive"
          onRemove={() => setIsConfirmingArchive(true)}
          onDiscard={() => {
            setName(category.name);
            setDescription(category.description);
            action.clearFailure();
          }}
          onSave={() =>
            void action.run(
              () =>
                onSave({
                  name,
                  description,
                  always_include: category.always_include,
                }),
              "Couldn’t save the category. Please try again.",
            )
          }
        />
      )}
    </FoldingCard>
  );
}
