import { FormEditor } from "@/components/FormEditor";
import type { CopySlot } from "@/lib/api-client";
import { formatLastSavedAt } from "@/lib/dates";

/**
 * Says who last saved a slot's text, and when.
 *
 * @param slot - The slot.
 * @returns "Seed text" while it has its seed text, otherwise a note like
 *   "Last saved 8 Nov 2026, 2:20 PM by Maya Lin".
 */
function lastSavedText(slot: CopySlot): string {
  if (!slot.updated_by) {
    return "Seed text";
  }
  return `Last saved ${formatLastSavedAt(slot.updated_at)} by ${slot.updated_by}`;
}

/**
 * The page id of a Copy slot's editor, so a search result can take the
 * Admin to it.
 *
 * @param key - The slot's key.
 * @returns The id.
 */
export function copySlotFieldId(key: string): string {
  return `copy-slot-${key}`;
}

/**
 * One Copy slot in the form template's short editor: its name, the
 * placeholders it takes and who last saved it along the top, with the
 * count against its max length, and the reason a save turned it away, if
 * one did, below.
 *
 * @param props - `slot` is the slot, `value` its current text, `error` why
 *   the last save turned it away (if it did) and `onChange` is called with
 *   the new text.
 * @returns The slot's editor.
 */
export function CopySlotField({
  slot,
  value,
  error,
  onChange,
}: {
  slot: CopySlot;
  value: string;
  error?: string;
  onChange: (text: string) => void;
}) {
  const errorId = `copy-${slot.key}-error`;
  const placeholders = slot.placeholders
    .map((name) => `{${name}}`)
    .join(" and ");

  return (
    <div
      id={copySlotFieldId(slot.key)}
      role="group"
      aria-label={slot.name}
      className="flex flex-col gap-1"
    >
      <FormEditor
        label={slot.name}
        size="short"
        maxLength={slot.max_length}
        describedById={error ? errorId : undefined}
        caption={
          <>
            <span className="text-text">{slot.name}</span>
            {placeholders ? (
              <>
                {" · "}
                <span>Takes {placeholders}</span>
              </>
            ) : null}
            {" · "}
            <span>{lastSavedText(slot)}</span>
          </>
        }
        value={value}
        onChange={onChange}
      />
      {error ? (
        <p id={errorId} role="alert" className="m-0 text-[13px] text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
