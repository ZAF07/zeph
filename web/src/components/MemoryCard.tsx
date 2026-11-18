import type { ReactNode } from "react";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";

/**
 * One card on a Memories tab: its content at the left and a delete button
 * at the top right.
 *
 * @param props - `deleteLabel` names the delete button for screen readers;
 *   `isDeleting` locks it; `onDelete` is called when it is pressed;
 *   `roomy` gives the 18px top and bottom padding most cards have instead
 *   of 16px; `children` is the content.
 * @returns The card.
 */
export function MemoryCard({
  deleteLabel,
  isDeleting,
  onDelete,
  roomy = true,
  children,
}: {
  deleteLabel: string;
  isDeleting: boolean;
  onDelete: () => void;
  roomy?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`box-border rounded-card border border-line bg-panel pr-3 pl-[22px] [overflow-wrap:anywhere] ${roomy ? "py-[18px]" : "py-4"}`}
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
