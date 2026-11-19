"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useId, useRef, useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { dialogSurface } from "@/components/dialog-styles";
import { fieldBox } from "@/components/field-styles";
import type { EvalCase } from "@/lib/api-client";
import { savingErrors } from "@/lib/eval-forms";
import { evalCaseEditHref } from "@/lib/evals";
import { refreshEvalCases } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * Asks for the key of a copy of an Eval Case, makes the copy, then opens it.
 * Drawn in the shared confirm dialog's shell, with one field. A native
 * `<dialog>` opened with `showModal()`, so Escape cancels.
 *
 * @param props - `evalCase` is the case to copy; `onClose` closes the
 *   dialog without copying.
 * @returns The dialog.
 */
export function EvalCaseDuplicateDialog({
  evalCase,
  onClose,
}: {
  evalCase: EvalCase;
  onClose: () => void;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const keyId = useId();
  const [copyKey, setCopyKey] = useState(`${evalCase.key}-copy`);

  const duplicateMutation = useMutation({
    mutationFn: (newKey: string) =>
      apiClient.duplicateEvalCase(evalCase.key, newKey),
    onSuccess: (copy) => {
      refreshEvalCases(queryClient);
      router.push(evalCaseEditHref(copy));
    },
  });
  const errors = savingErrors(duplicateMutation.error);
  const error = errors.fields.key ?? errors.summary;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog !== null && !dialog.open) {
      dialog.showModal();
    }
  }, []);

  function duplicate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    duplicateMutation.mutate(copyKey.trim());
  }

  return (
    <dialog
      ref={dialogRef}
      aria-label={`Duplicate ${evalCase.key}`}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      className={`m-auto w-[calc(100%-32px)] max-w-[460px] ${dialogSurface}`}
    >
      <form onSubmit={duplicate} className="flex flex-col gap-3 px-7 py-[26px]">
        <h2 className="m-0 text-[20px] font-normal text-cream">
          Duplicate {evalCase.key}
        </h2>
        <label htmlFor={keyId} className="text-[13px] text-soft">
          Key for the copy
        </label>
        <span className={fieldBox}>
          <input
            id={keyId}
            value={copyKey}
            onChange={(event) => setCopyKey(event.target.value)}
            className="min-h-11 w-full min-w-0 border-0 bg-transparent p-0 text-[15px] text-text"
          />
        </span>
        {error ? (
          <p role="alert" className="m-0 text-[13px] text-danger">
            {error}
          </p>
        ) : null}
        <div className="flex flex-wrap justify-end gap-2 pt-1.5">
          <button type="button" className={secondaryButton} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={primaryButton}
            disabled={duplicateMutation.isPending}
          >
            Duplicate
          </button>
        </div>
      </form>
    </dialog>
  );
}
