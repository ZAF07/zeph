import type { ReactNode } from "react";

import { primaryButton } from "@/components/button-styles";

const textButton =
  "min-h-11 cursor-pointer border-0 bg-transparent px-2.5 text-[13px] text-text underline";

/**
 * The row above a card list: how many there are, Expand all and Collapse
 * all, and the add button.
 *
 * @param props - `count` is the count line, such as "6 kinds"; `onExpandAll`
 *   and `onCollapseAll` open and fold every card; `addLabel`, `onAdd` and
 *   `isAddDisabled` are the add button.
 * @returns The toolbar.
 */
export function CardListToolbar({
  count,
  onExpandAll,
  onCollapseAll,
  addLabel,
  onAdd,
  isAddDisabled = false,
}: {
  count: ReactNode;
  onExpandAll: () => void;
  onCollapseAll: () => void;
  addLabel?: string;
  onAdd?: () => void;
  isAddDisabled?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
        <span className="text-[14px] text-soft">{count}</span>
        <span aria-hidden="true" className="h-4 w-px bg-line" />
        <button type="button" className={textButton} onClick={onExpandAll}>
          Expand all
        </button>
        <button type="button" className={textButton} onClick={onCollapseAll}>
          Collapse all
        </button>
      </div>
      {addLabel && onAdd ? (
        <button
          type="button"
          className={primaryButton}
          disabled={isAddDisabled}
          onClick={onAdd}
        >
          {addLabel}
        </button>
      ) : null}
    </div>
  );
}
