import { dangerButton, secondaryButton } from "@/components/button-styles";

/**
 * The remove confirm shown inside an open card, in place of its save bar.
 * The safe choice comes first.
 *
 * @param props - `label` names the confirm for screen readers; `title` and
 *   `body` say what will go; `keepLabel` and `confirmLabel` name the two
 *   buttons; `isBusy` stops a second press; `onKeep` and `onConfirm` are
 *   the choices.
 * @returns The confirm.
 */
export function CardRemoveConfirm({
  label,
  title,
  body,
  keepLabel = "Keep it",
  confirmLabel = "Remove",
  isBusy = false,
  onKeep,
  onConfirm,
}: {
  label: string;
  title: string;
  body: string;
  keepLabel?: string;
  confirmLabel?: string;
  isBusy?: boolean;
  onKeep: () => void;
  onConfirm: () => void;
}) {
  return (
    <div
      role="alertdialog"
      aria-label={label}
      className="box-border flex flex-col gap-2.5 rounded-tile border border-danger px-5 py-4"
    >
      <div className="text-[15px] font-normal text-text">{title}</div>
      <p className="m-0 text-[13px] text-soft">{body}</p>
      <div className="flex flex-wrap justify-end gap-2">
        <button
          type="button"
          className={secondaryButton}
          disabled={isBusy}
          onClick={onKeep}
        >
          {keepLabel}
        </button>
        <button
          type="button"
          className={dangerButton}
          disabled={isBusy}
          onClick={onConfirm}
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  );
}
