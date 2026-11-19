import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";

/** A message about the last change to a card list, and whether it failed. */
export type Flash = { text: string; isError: boolean };

/**
 * The note above a card list after a change: the shared saved note, or the
 * shared failed note.
 *
 * @param props - `flash` is the message, or null for none.
 * @returns The note, or nothing.
 */
export function CardListFlash({ flash }: { flash: Flash | null }) {
  if (!flash) {
    return null;
  }
  return flash.isError ? (
    <SaveFailedNote>{flash.text}</SaveFailedNote>
  ) : (
    <SavedNote>{flash.text}</SavedNote>
  );
}
