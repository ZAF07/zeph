import type { MoveDirection } from "@/lib/api-client";

const arrowButton =
  "inline-flex size-11 cursor-pointer items-center justify-center rounded-pill border border-line-strong bg-transparent text-text disabled:cursor-not-allowed disabled:text-mute";

/**
 * Move up and Move down for a card in an ordered list, at the left of its
 * save bar.
 *
 * @param props - `name` names the item for screen readers; `canMoveUp` and
 *   `canMoveDown` say which ways it can go; `isMoving` turns both off while
 *   a move saves; `onMove` moves it.
 * @returns The two buttons.
 */
export function CardMoveButtons({
  name,
  canMoveUp,
  canMoveDown,
  isMoving,
  onMove,
}: {
  name: string;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isMoving: boolean;
  onMove: (direction: MoveDirection) => void;
}) {
  return (
    <span className="inline-flex gap-1.5">
      <button
        type="button"
        aria-label={`Move ${name} up`}
        className={arrowButton}
        disabled={!canMoveUp || isMoving}
        onClick={() => onMove("up")}
      >
        ↑
      </button>
      <button
        type="button"
        aria-label={`Move ${name} down`}
        className={arrowButton}
        disabled={!canMoveDown || isMoving}
        onClick={() => onMove("down")}
      >
        ↓
      </button>
    </span>
  );
}
