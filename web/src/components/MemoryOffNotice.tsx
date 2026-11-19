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
 *   `onTurnOn` turns User Memory back on and `turnOnLabel` is the button's
 *   words; without them there is no button (as on Account, where the
 *   switch beside the notice does that).
 * @returns The notice, or nothing.
 */
export function MemoryOffNotice({
  note,
  canTurnOn,
  isSaving = false,
  onTurnOn,
  turnOnLabel,
}: {
  note: string;
  canTurnOn: boolean;
  isSaving?: boolean;
  onTurnOn?: () => void;
  turnOnLabel?: string;
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
          canTurnOn && onTurnOn && turnOnLabel ? (
            <button
              type="button"
              className={secondaryButton}
              disabled={isSaving}
              onClick={onTurnOn}
            >
              {turnOnLabel}
            </button>
          ) : undefined
        }
      />
    </div>
  );
}
