"use client";

import { useEffect, useMemo, useRef } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { dialogSurface } from "@/components/dialog-styles";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { compareTexts } from "@/lib/text-changes";

/**
 * The "Review changes" dialog: the saved and edited text compared word by
 * word, with additions and removals highlighted, then "Save and re-index"
 * or "Keep editing". Escape keeps editing, unless a save is under way.
 *
 * @param props - `saved` and `edited` are the texts to compare; `isSaving`
 *   shows the save is under way; `error` is why the last save failed;
 *   `onConfirm` saves; `onCancel` closes the dialog.
 * @returns The dialog.
 */
export function TextChangesReview({
  saved,
  edited,
  isSaving,
  error,
  onConfirm,
  onCancel,
}: {
  saved: string;
  edited: string;
  isSaving: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const confirmRef = useRef<HTMLButtonElement>(null);
  const comparison = useMemo(
    () => compareTexts(saved, edited),
    [saved, edited],
  );

  useEffect(() => {
    confirmRef.current?.focus();
  }, []);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSaving) {
        onCancel();
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isSaving, onCancel]);

  return (
    <div className="fixed inset-0 z-[400] flex items-center justify-center bg-black/60 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-changes-heading"
        className={`flex max-h-[min(90vh,820px)] w-full max-w-[860px] flex-col gap-4 px-7 py-[26px] ${dialogSurface}`}
      >
        <div className="flex flex-col gap-1">
          <h2
            id="review-changes-heading"
            className="m-0 text-[20px] font-normal text-cream"
          >
            Review changes
          </h2>
          <p className="m-0 text-[14px] text-soft">
            {comparison.addedWords}{" "}
            {comparison.addedWords === 1 ? "word" : "words"} added ·{" "}
            {comparison.removedWords}{" "}
            {comparison.removedWords === 1 ? "word" : "words"} removed. Saving
            re-indexes the document; Zeph doesn’t use it until it’s Ready again.
          </p>
        </div>
        <div
          aria-label="Changes"
          className="min-h-0 flex-1 overflow-y-auto whitespace-pre-wrap break-words rounded-input border border-line bg-panel p-4 font-mono text-[13px] leading-relaxed text-text"
        >
          {comparison.parts.map((part, index) => {
            if (part.kind === "skipped") {
              return (
                <span
                  key={index}
                  className="mx-1 inline-block rounded-[6px] bg-bg-deep px-1.5 font-sans text-[12px] text-soft"
                >
                  {part.characters.toLocaleString("en-GB")} unchanged characters
                </span>
              );
            }
            if (part.kind === "added") {
              return (
                <ins
                  key={index}
                  className="rounded-[4px] bg-zeph text-cream no-underline"
                >
                  {part.text}
                </ins>
              );
            }
            if (part.kind === "removed") {
              return (
                <del
                  key={index}
                  className="rounded-[4px] text-danger line-through"
                >
                  {part.text}
                </del>
              );
            }
            return <span key={index}>{part.text}</span>;
          })}
        </div>
        {error ? <SaveFailedNote>{error}</SaveFailedNote> : null}
        <div className="flex flex-wrap gap-3">
          <button
            ref={confirmRef}
            type="button"
            className={primaryButton}
            disabled={isSaving}
            onClick={onConfirm}
          >
            {isSaving ? "Saving…" : "Save and re-index"}
          </button>
          <button
            type="button"
            className={secondaryButton}
            disabled={isSaving}
            onClick={onCancel}
          >
            Keep editing
          </button>
        </div>
      </div>
    </div>
  );
}
