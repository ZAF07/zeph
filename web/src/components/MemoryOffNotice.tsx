import { secondaryButton } from "@/components/button-styles";
import { PausedNotice } from "@/components/PausedNotice";

/**
 * The Admin-worded note saying User Memory is off and why, drawn as the
 * design's "Memory is off" notice. When the note opens with words between
 * double asterisks, they are its title and the rest its body; otherwise the
 * whole note is the title.
 *
 * @param props - `note` is the note the backend sent, "" while User Memory
 *   is on, which shows nothing; `canTurnOn` is false when an Admin has User
 *   Memory off, which hides "Turn memory on"; `isSaving` locks the button;
 *   `onTurnOn` turns User Memory back on.
 * @returns The notice, or nothing.
 */
export function MemoryOffNotice({
  note,
  canTurnOn,
  isSaving,
  onTurnOn,
}: {
  note: string;
  canTurnOn: boolean;
  isSaving: boolean;
  onTurnOn: () => void;
}) {
  if (!note) {
    return null;
  }
  const [before, title, ...rest] = note.split("**");
  const hasTitle = before === "" && title !== undefined;
  return (
    <div role="status">
      <PausedNotice
        title={hasTitle ? title : note}
        body={hasTitle ? rest.join("") : ""}
        action={
          canTurnOn ? (
            <button
              type="button"
              className={secondaryButton}
              disabled={isSaving}
              onClick={onTurnOn}
            >
              Turn memory on
            </button>
          ) : undefined
        }
      />
    </div>
  );
}
