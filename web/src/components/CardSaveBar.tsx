import type { ReactNode } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { SaveFailedNote } from "@/components/SaveFailedNote";

const removeButton =
  "min-h-11 cursor-pointer border-0 bg-transparent px-3 text-[14px] text-danger disabled:cursor-not-allowed disabled:text-mute";

/**
 * The save bar at the foot of an open card: a note on when changes apply
 * (or why the last save failed), then Remove, Discard and Save, always in
 * the same place.
 *
 * @param props - `note` says when changes apply; `leading` goes before the
 *   note, such as move up and down; `failedMessage` replaces the note when
 *   a save failed; `isDirty`, `canSave` and `isBusy` set which buttons
 *   work; `removeLabel` and `onRemove` are the remove button, if there is
 *   one; `actions` are other buttons before Discard; `onDiscard` and
 *   `onSave` are the other two (none when the card has nothing to save).
 * @returns The bar.
 */
export function CardSaveBar({
  note,
  leading,
  failedMessage,
  isDirty = false,
  canSave = false,
  isBusy = false,
  removeLabel = "Remove",
  onRemove,
  actions,
  onDiscard,
  onSave,
}: {
  note: ReactNode;
  leading?: ReactNode;
  failedMessage?: string | null;
  isDirty?: boolean;
  canSave?: boolean;
  isBusy?: boolean;
  removeLabel?: string;
  onRemove?: () => void;
  actions?: ReactNode;
  onDiscard?: () => void;
  onSave?: () => void;
}) {
  const hasFailed = Boolean(failedMessage) && !isBusy;
  let saveText = "Save";
  if (isBusy) {
    saveText = "Saving…";
  } else if (hasFailed) {
    saveText = "Try again";
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2.5 border-t border-line pt-[14px]">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        {leading}
        {hasFailed ? (
          <SaveFailedNote>{failedMessage}</SaveFailedNote>
        ) : (
          <span className="text-[13px] text-soft">{note}</span>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {onRemove ? (
          <button
            type="button"
            className={removeButton}
            disabled={isBusy}
            onClick={onRemove}
          >
            {removeLabel}
          </button>
        ) : null}
        {actions}
        {onDiscard ? (
          <button
            type="button"
            className={secondaryButton}
            disabled={!isDirty || isBusy}
            onClick={onDiscard}
          >
            Discard
          </button>
        ) : null}
        {onSave ? (
          <button
            type="button"
            className={primaryButton}
            disabled={!canSave || isBusy}
            onClick={onSave}
          >
            {saveText}
          </button>
        ) : null}
      </div>
    </div>
  );
}
