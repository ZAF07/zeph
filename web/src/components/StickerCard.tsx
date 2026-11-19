"use client";

import { useState } from "react";

import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { CardTextField } from "@/components/CardTextField";
import { FoldingCard } from "@/components/FoldingCard";
import { StickerPicture } from "@/components/StickerPicture";
import type { Sticker } from "@/lib/api-client";
import { useCardAction } from "@/lib/use-card-action";

/**
 * Names a sticker by its emoji and set, like "🌱 CalmCreatures".
 *
 * @param sticker - The sticker.
 * @returns Its name for the card's title.
 */
function stickerTitle(sticker: Sticker): string {
  return [sticker.emoji, sticker.set_name ?? "Single sticker"]
    .filter(Boolean)
    .join(" ");
}

/**
 * One sticker in the Sticker Library as a card of the card list. The
 * folded row shows its picture, emoji and set, and the start of its "when
 * to use" note, or "Needs a note", because Zeph won't send it without one.
 * Open, it has the note and the save bar with Remove.
 *
 * @param props - `sticker` is the sticker as saved; `isOpen` and
 *   `onToggle` open and fold it; `onSaveNote` saves the note and rejects
 *   if that fails; `onRemove` removes it and rejects if that fails.
 * @returns The card.
 */
export function StickerCard({
  sticker,
  isOpen,
  onToggle,
  onSaveNote,
  onRemove,
}: {
  sticker: Sticker;
  isOpen: boolean;
  onToggle: () => void;
  onSaveNote: (note: string) => Promise<void>;
  onRemove: () => Promise<void>;
}) {
  const [note, setNote] = useState(sticker.note);
  const [isConfirmingRemove, setIsConfirmingRemove] = useState(false);
  const action = useCardAction();
  const isDirty = note !== sticker.note;
  const title = stickerTitle(sticker);

  return (
    <FoldingCard
      title={title}
      summary={sticker.note || "No note yet"}
      leading={<StickerPicture sticker={sticker} />}
      tags={sticker.note ? null : <CardTag tone="orange">Needs a note</CardTag>}
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <CardTextField
        label="When to use"
        placeholder="e.g. a warm good-morning"
        value={note}
        multiline
        onChange={(next) => {
          setNote(next);
          action.clearFailure();
        }}
      />
      {isConfirmingRemove ? (
        <CardRemoveConfirm
          label="Remove this sticker?"
          title={`Remove ${title}?`}
          body="Zeph stops sending it."
          isBusy={action.isBusy}
          onKeep={() => setIsConfirmingRemove(false)}
          onConfirm={async () => {
            await action.run(onRemove, "Couldn’t remove. Try again.");
            setIsConfirmingRemove(false);
          }}
        />
      ) : (
        <CardSaveBar
          note="Zeph reads this note to choose a sticker, and uses them sparingly."
          failedMessage={action.failedMessage}
          isDirty={isDirty}
          canSave={isDirty}
          isBusy={action.isBusy}
          onRemove={() => setIsConfirmingRemove(true)}
          onDiscard={() => {
            setNote(sticker.note);
            action.clearFailure();
          }}
          onSave={() =>
            void action.run(() => onSaveNote(note), "Couldn’t save. Try again.")
          }
        />
      )}
    </FoldingCard>
  );
}
