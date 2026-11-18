import type { ReactNode } from "react";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";

/**
 * One card on a Memories tab: its content at the left and a delete button
 * at the top right.
 *
 * @param props - `deleteLabel` names the delete button for screen readers;
 *   `isDeleting` locks it; `onDelete` is called when it is pressed;
 *   `compact` gives 16px top and bottom padding instead of the 18px most
 *   cards have; `children` is the content.
 * @returns The card.
 */
export function MemoryCard({
  deleteLabel,
  isDeleting,
  onDelete,
  compact = false,
  children,
}: {
  deleteLabel: string;
  isDeleting: boolean;
  onDelete: () => void;
  compact?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`box-border rounded-card border border-line bg-panel pr-3 pl-[22px] [overflow-wrap:anywhere] ${compact ? "py-4" : "py-[18px]"}`}
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
    </div>
  );
}
