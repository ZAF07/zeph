import { secondaryButton } from "@/components/button-styles";
import { PausedNotice } from "@/components/PausedNotice";
import type { MemoryOffNote } from "@/lib/memory-off-note";

/**
 * The note saying User Memory is off and why, drawn as the design's "Memory
 * is off" notice.
 *
 * @param props - `note` is the note's title and body, or null while User
 *   Memory is on, which shows nothing; `canTurnOn` is false when an Admin
 *   has User Memory off, which hides "Turn memory on"; `isSaving` locks the
 *   button; `onTurnOn` turns User Memory back on and `turnOnLabel` is the
 *   button's words; without them there is no button (as on Account, where
 *   the switch beside the notice does that).
 * @returns The notice, or nothing.
 */
export function MemoryOffNotice({
  note,
  canTurnOn,
  isSaving = false,
  onTurnOn,
  turnOnLabel,
}: {
  note: MemoryOffNote | null;
  canTurnOn: boolean;
  isSaving?: boolean;
  onTurnOn?: () => void;
  turnOnLabel?: string;
}) {
  if (!note) {
    return null;
  }
  return (
    <div role="status">
      <PausedNotice
        title={note.title}
        body={note.body}
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
