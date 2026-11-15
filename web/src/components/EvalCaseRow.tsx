"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import {
  compactSecondaryButton,
  primaryButton,
  secondaryButton,
} from "@/components/button-styles";
import { EvalPill } from "@/components/EvalPill";
import { fieldLabel, inputField } from "@/components/form-styles";
import type { EvalCase } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import { savingErrors } from "@/lib/eval-forms";
import { refreshEvalCases } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * One Eval Case in its Eval's list: its key, whether it was edited or is
 * archived, who last changed it, and Duplicate and Archive. Duplicate asks
 * for the copy's key, then opens the copy; Archive asks to confirm first.
 *
 * @param props - `evalCase` is the case.
 * @returns The row.
 */
export function EvalCaseRow({ evalCase }: { evalCase: EvalCase }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [step, setStep] = useState<"idle" | "duplicate" | "archive">("idle");
  const [copyKey, setCopyKey] = useState(`${evalCase.key}-copy`);
  const editHref = `/admin/evals/cases/${evalCase.eval}/edit/${evalCase.key}`;

  const duplicateMutation = useMutation({
    mutationFn: (newKey: string) =>
      apiClient.duplicateEvalCase(evalCase.key, newKey),
    onSuccess: (copy) => {
      refreshEvalCases(queryClient);
      router.push(`/admin/evals/cases/${copy.eval}/edit/${copy.key}`);
    },
  });
  const archiveMutation = useMutation({
    mutationFn: () => apiClient.archiveEvalCase(evalCase.key),
    onSuccess: () => {
      refreshEvalCases(queryClient);
      setStep("idle");
    },
  });
  const duplicateErrors = savingErrors(duplicateMutation.error);
  const duplicateError = duplicateErrors.fields.key ?? duplicateErrors.summary;

  function duplicate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    duplicateMutation.mutate(copyKey.trim());
  }

  return (
    <li className="flex flex-col gap-3 border-b border-line px-[18px] py-3.5 last:border-b-0">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <span className="flex flex-wrap items-center gap-2">
            <Link href={editHref} className="font-mono text-sm font-medium">
              {evalCase.key}
            </Link>
            {evalCase.archived ? (
              <EvalPill label="Archived" pill="bg-subtle text-ink-body" />
            ) : null}
            {evalCase.edited ? (
              <EvalPill label="Edited" pill="bg-blue-tint text-blue-deep" />
            ) : null}
          </span>
          <span className="text-caption text-ink-muted">
            {evalCase.updated_by_name
              ? `Changed ${formatSavedAt(evalCase.updated_at)} by ${evalCase.updated_by_name}`
              : "From the seed files"}
          </span>
        </div>
        {step === "idle" ? (
          <div className="flex flex-wrap gap-2">
            <Link href={editHref} className={compactSecondaryButton}>
              {evalCase.archived ? "View" : "Edit"}
            </Link>
            <button
              type="button"
              className={compactSecondaryButton}
              onClick={() => setStep("duplicate")}
            >
              Duplicate
            </button>
            {evalCase.archived ? null : (
              <button
                type="button"
                className={compactSecondaryButton}
                onClick={() => setStep("archive")}
              >
                Archive
              </button>
            )}
          </div>
        ) : null}
      </div>

      {step === "duplicate" ? (
        <form
          onSubmit={duplicate}
          className="flex flex-wrap items-end gap-3 rounded-xl bg-subtle p-4"
        >
          <label className={`${fieldLabel} flex-[1_1_260px]`}>
            Key for the copy
            <input
              className={inputField}
              value={copyKey}
              onChange={(event) => setCopyKey(event.target.value)}
            />
          </label>
          <button
            type="submit"
            className={primaryButton}
            disabled={duplicateMutation.isPending}
          >
            Duplicate
          </button>
          <button
            type="button"
            className={secondaryButton}
            onClick={() => setStep("idle")}
          >
            Cancel
          </button>
          {duplicateError ? (
            <p role="alert" className="m-0 w-full text-caption text-danger">
              {duplicateError}
            </p>
          ) : null}
        </form>
      ) : null}

      {step === "archive" ? (
        <div className="flex flex-wrap items-center gap-3 rounded-xl bg-subtle p-4">
          <p className="m-0 flex-[1_1_260px] text-sm">
            Archive {evalCase.key}? New runs leave it out; past runs still show
            it. Archived cases can’t be edited.
          </p>
          <button
            type="button"
            className={primaryButton}
            disabled={archiveMutation.isPending}
            onClick={() => archiveMutation.mutate()}
          >
            Archive
          </button>
          <button
            type="button"
            className={secondaryButton}
            onClick={() => setStep("idle")}
          >
            Keep it
          </button>
          {archiveMutation.isError ? (
            <p role="alert" className="m-0 w-full text-caption text-danger">
              Couldn’t archive the case. Try again.
            </p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
