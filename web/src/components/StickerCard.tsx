"use client";

import { useState } from "react";

import { quietButton } from "@/components/button-styles";
import { StickerPicture } from "@/components/StickerPicture";
import type { Sticker } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type NoteStatus = "idle" | "saving" | "saved" | "failed";

/**
 * One sticker in the Sticker Library: its image and emoji, its "when to
 * use" note, saved when the Admin leaves the field, and Remove. A sticker
 * without a note is marked "Needs a note", because Zeph won't send it.
 *
 * @param props - `sticker` is the sticker; `onRemove` removes it and
 *   rejects if that fails.
 * @returns The card.
 */
export function StickerCard({
  sticker,
  onRemove,
}: {
  sticker: Sticker;
  onRemove: () => Promise<void>;
}) {
  const apiClient = useApiClient();
  const [savedNote, setSavedNote] = useState(sticker.note);
  const [draftNote, setDraftNote] = useState(sticker.note);
  const [noteStatus, setNoteStatus] = useState<NoteStatus>("idle");
  const [isRemoving, setIsRemoving] = useState(false);
  const [removeFailed, setRemoveFailed] = useState(false);

  async function saveNote() {
    if (draftNote.trim() === savedNote) {
      return;
    }
    setNoteStatus("saving");
    try {
      const saved = await apiClient.saveStickerNote(sticker.id, draftNote);
      setSavedNote(saved.note);
      setDraftNote(saved.note);
      setNoteStatus("saved");
    } catch {
      setNoteStatus("failed");
    }
  }

  async function remove() {
    setIsRemoving(true);
    setRemoveFailed(false);
    try {
      await onRemove();
    } catch {
      setRemoveFailed(true);
      setIsRemoving(false);
    }
  }

  return (
    <li className="flex flex-col gap-2.5 rounded-2xl border border-line bg-white p-3.5">
      <StickerPicture sticker={sticker} />
      <div className="flex items-center justify-between gap-2">
        <span
          aria-label={`Emoji: ${sticker.emoji ?? "none"}`}
          className="inline-flex items-center rounded-full bg-code px-2.5 py-0.5 text-base"
        >
          {sticker.emoji}
        </span>
        {savedNote ? null : (
          <span className="inline-flex items-center rounded-full bg-yellow-tint px-2.5 py-0.5 text-xs font-medium text-yellow-deep">
            Needs a note
          </span>
        )}
      </div>
      <label className="flex min-w-0 flex-col gap-2 text-xs font-medium">
        When to use
        <textarea
          rows={2}
          value={draftNote}
          placeholder="e.g. a warm good-morning"
          onChange={(event) => {
            setDraftNote(event.target.value);
            setNoteStatus("idle");
          }}
          onBlur={() => void saveNote()}
          className="min-h-14 w-full resize-y rounded-input border border-line-strong bg-white px-2.5 py-2 text-[13px] font-normal leading-normal text-ink"
        />
      </label>
      <p role="status" className="m-0 min-h-4 text-xs text-ink-muted">
        {noteStatus === "saving" ? "Saving…" : null}
        {noteStatus === "saved" ? "Saved" : null}
        {noteStatus === "failed" ? (
          <span className="text-danger">Couldn’t save. Try again.</span>
        ) : null}
        {removeFailed ? (
          <span className="text-danger">Couldn’t remove. Try again.</span>
        ) : null}
      </p>
      <button
        type="button"
        className={`${quietButton} min-h-9 self-start text-danger`}
        disabled={isRemoving}
        onClick={() => void remove()}
      >
        Remove
      </button>
    </li>
  );
}
