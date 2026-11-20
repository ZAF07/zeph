import { primaryButton, secondaryButton } from "@/components/button-styles";
import { UnsavedTag } from "@/components/UnsavedTag";

/** The bar's own look: on its own panel, or the foot of an editor box. */
const placementClass = {
  alone: "rounded-tile border border-line bg-panel",
  inside: "border-t border-line",
};

/**
 * The form template's save bar, in the state the AdminPersona design draws
 * for it: nothing changed, unsaved changes, saving, or couldn't save (with
 * Discard and Try again).
 *
 * @param props - `isDirty` is whether there are edits; `isSaving` whether a
 *   save is under way; `failedMessage` says why the last save failed, or is
 *   null; `canSave` is whether the edits may be saved; `saveLabel` names the
 *   Save button; `placement` puts the bar on its own panel or at the foot of
 *   a box; `sticky` keeps it in view at the bottom while the page scrolls;
 *   `idleNote` is the line shown while nothing changed; `onDiscard` and
 *   `onSave` are the buttons' actions.
 * @returns The bar.
 */
export function SaveBar({
  isDirty,
  isSaving,
  failedMessage,
  canSave,
  saveLabel,
  placement,
  sticky = false,
  idleNote = "Changes apply to the next message after saving.",
  onDiscard,
  onSave,
}: {
  isDirty: boolean;
  isSaving: boolean;
  failedMessage: string | null;
  canSave: boolean;
  saveLabel: string;
  placement: "alone" | "inside";
  sticky?: boolean;
  idleNote?: string;
  onDiscard: () => void;
  onSave: () => void;
}) {
  const hasFailed = failedMessage !== null && !isSaving;
  let saveText = saveLabel;
  if (isSaving) {
    saveText = "Saving…";
  } else if (hasFailed) {
    saveText = "Try again";
  }

  let state = <span className="text-[13px] text-soft">{idleNote}</span>;
  if (hasFailed) {
    state = (
      <span role="alert" className="text-[13px] text-danger">
        {failedMessage}
      </span>
    );
  } else if (isDirty) {
    state = <UnsavedTag />;
  }

  return (
    <div
      role="group"
      aria-label="Save changes"
      className={`flex flex-wrap items-center justify-between gap-3 px-5 py-3 ${placementClass[placement]} ${sticky ? "sticky bottom-4" : ""}`}
    >
      {state}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={secondaryButton}
          disabled={!isDirty || isSaving}
          onClick={onDiscard}
        >
          Discard
        </button>
        <button
          type="button"
          className={primaryButton}
          disabled={!canSave || isSaving}
          onClick={onSave}
        >
          {saveText}
        </button>
      </div>
    </div>
  );
}
