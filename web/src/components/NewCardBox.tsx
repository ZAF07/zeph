import type { ReactNode } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { SaveFailedNote } from "@/components/SaveFailedNote";

/**
 * The box for adding a new item, shown above a card list: its title and
 * "Not saved yet", the fields, then Cancel and Add.
 *
 * @param props - `title` names it; `status` is the line beside the title,
 *   or null for none; `children` are the fields;
 *   `failedMessage` says why adding failed; `canAdd` and `isBusy` set
 *   whether Add works; `addLabel` names it and `busyLabel` replaces it while
 *   adding; `onCancel` and `onAdd` are the
 *   buttons (no Add when the fields bring their own).
 * @returns The box.
 */
export function NewCardBox({
  title,
  status = "Not saved yet",
  children,
  failedMessage = null,
  canAdd = false,
  isBusy = false,
  addLabel = "Add",
  busyLabel = "Adding…",
  onCancel,
  onAdd,
}: {
  title: string;
  status?: string | null;
  children: ReactNode;
  failedMessage?: string | null;
  canAdd?: boolean;
  isBusy?: boolean;
  addLabel?: string;
  busyLabel?: string;
  onCancel: () => void;
  onAdd?: () => void;
}) {
  return (
    <section
      aria-label={title}
      className="box-border flex flex-col gap-[14px] rounded-card border border-cream bg-panel px-5 py-[18px]"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[16px] font-normal text-cream">{title}</span>
        {status ? (
          <span className="text-[12px] text-soft">{status}</span>
        ) : null}
      </div>
      {children}
      {failedMessage && !isBusy ? (
        <SaveFailedNote>{failedMessage}</SaveFailedNote>
      ) : null}
      <div className="flex flex-wrap justify-end gap-2 border-t border-line pt-[14px]">
        <button
          type="button"
          className={secondaryButton}
          disabled={isBusy}
          onClick={onCancel}
        >
          Cancel
        </button>
        {onAdd ? (
          <button
            type="button"
            className={primaryButton}
            disabled={!canAdd || isBusy}
            onClick={onAdd}
          >
            {isBusy ? busyLabel : addLabel}
          </button>
        ) : null}
      </div>
    </section>
  );
}
