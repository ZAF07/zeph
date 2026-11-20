import type { ReactNode } from "react";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";

/**
 * One card on a Memories tab: its content at the left and a delete button
 * at the top right, with anything in `below` under them across the card.
 *
 * @param props - `deleteLabel` names the delete button for screen readers;
 *   `isDeleting` locks it; `onDelete` is called when it is pressed;
 *   `compact` gives 16px top and bottom padding instead of the 18px most
 *   cards have; `children` is the content; `below` goes under the content
 *   and delete button, and gives the card 16px top and 8px bottom padding.
 * @returns The card.
 */
export function MemoryCard({
  deleteLabel,
  isDeleting,
  onDelete,
  compact = false,
  children,
  below,
}: {
  deleteLabel: string;
  isDeleting: boolean;
  onDelete: () => void;
  compact?: boolean;
  children: ReactNode;
  below?: ReactNode;
}) {
  let padding = "py-[18px]";
  if (below) {
    padding = "pt-4 pb-2";
  } else if (compact) {
    padding = "py-4";
  }
  return (
    <div
      className={`box-border rounded-card border border-line bg-panel pr-3 pl-[22px] [overflow-wrap:anywhere] ${padding}`}
    >
      <div className="flex items-start justify-between gap-3">
        {children}
        <button
          type="button"
          aria-label={deleteLabel}
          className={deleteIconButton}
          disabled={isDeleting}
          onClick={onDelete}
        >
          <DeleteIcon />
        </button>
      </div>
      {below}
    </div>
  );
}
