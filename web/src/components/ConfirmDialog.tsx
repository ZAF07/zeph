"use client";

import { useEffect, useRef } from "react";

import { dangerButton, secondaryButton } from "@/components/button-styles";
import { dialogSurface } from "@/components/dialog-styles";

/**
 * Asks before something that can't be undone. The safe choice comes first,
 * and the dialog names exactly what will go.
 *
 * It is a native `<dialog>` opened with `showModal()`, so the browser keeps
 * focus inside it, puts focus on the safe choice, and closes it on Escape
 * (which counts as cancel). With `modal` false it is drawn in place instead,
 * as on the design's `States` sheet.
 *
 * @param props - `open` shows it; `title` and `body` say what will go;
 *   `cancelLabel` and `confirmLabel` name the two buttons; `onConfirm` and
 *   `onCancel` are called when the person chooses; `modal` (default true)
 *   opens it over the page.
 * @returns The dialog.
 */
export function ConfirmDialog({
  open,
  title,
  body,
  cancelLabel,
  confirmLabel,
  onConfirm,
  onCancel,
  modal = true,
}: {
  open: boolean;
  title: string;
  body: string;
  cancelLabel: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  modal?: boolean;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!modal || dialog === null) {
      return;
    }
    if (open && !dialog.open) {
      dialog.showModal();
    }
    if (!open && dialog.open) {
      dialog.close();
    }
  }, [open, modal]);

  return (
    <dialog
      ref={dialogRef}
      role="alertdialog"
      aria-label={title}
      open={modal ? undefined : open}
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      className={`${modal ? "m-auto w-[calc(100%-32px)]" : "static m-0 w-full"} max-w-[460px] ${dialogSurface}`}
    >
      <div className="flex flex-col gap-3 px-7 py-[26px]">
        <h2 className="m-0 text-[20px] font-normal text-cream">{title}</h2>
        <p className="m-0 text-[14px] text-soft">{body}</p>
        <div className="flex flex-wrap justify-end gap-2 pt-1.5">
          <button type="button" className={secondaryButton} onClick={onCancel}>
            {cancelLabel}
          </button>
          <button type="button" className={dangerButton} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
