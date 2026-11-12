"use client";

import { useState } from "react";

import {
  confirmDangerButton,
  secondaryButton,
} from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";

/** The word a User types to confirm a deletion. */
const confirmationWord = "DELETE";

/**
 * Asks the User to type DELETE before a deletion that can't be undone.
 *
 * @param props - `confirmLabel` and `cancelLabel` name the two buttons;
 *   `isDeleting` locks them while the deletion runs; `onConfirm` and
 *   `onCancel` are called when the buttons are pressed.
 * @returns The confirmation box.
 */
export function DeleteConfirmation({
  confirmLabel,
  cancelLabel,
  isDeleting,
  onConfirm,
  onCancel,
}: {
  confirmLabel: string;
  cancelLabel: string;
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const [typedWord, setTypedWord] = useState("");

  return (
    <div className="flex flex-col gap-3 rounded-card bg-danger-tint p-5">
      <label className={fieldLabel}>
        Type DELETE to confirm
        <input
          className={`${inputField} max-w-[320px]`}
          type="text"
          autoComplete="off"
          value={typedWord}
          onChange={(event) => setTypedWord(event.target.value)}
        />
      </label>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={confirmDangerButton}
          disabled={typedWord !== confirmationWord || isDeleting}
          onClick={onConfirm}
        >
          {isDeleting ? "Deleting…" : confirmLabel}
        </button>
        <button
          type="button"
          className={secondaryButton}
          disabled={isDeleting}
          onClick={onCancel}
        >
          {cancelLabel}
        </button>
      </div>
    </div>
  );
}
