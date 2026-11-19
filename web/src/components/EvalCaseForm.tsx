"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldCaption, inputField } from "@/components/form-styles";
import { ShapeFormSections } from "@/components/ShapeFormSections";
import type {
  EvalCase,
  EvalName,
  FormShape,
  FormValues,
} from "@/lib/api-client";
import { emptyForm, savingErrors } from "@/lib/eval-forms";
import { queryKeys, refreshEvalCases } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The form for one Eval Case, in sections drawn from its Eval's case shape.
 * A new case also asks for its key. A save the backend refuses shows its
 * message beside each field that is wrong. An archived case is shown but
 * can't be changed.
 *
 * @param props - `evalName` is its Eval, `shape` its case shape and
 *   `existing` the case being edited, or undefined for a new one.
 * @returns The form.
 */
export function EvalCaseForm({
  evalName,
  shape,
  existing,
}: {
  evalName: EvalName;
  shape: FormShape;
  existing?: EvalCase;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [caseKey, setCaseKey] = useState(existing?.key ?? "");
  const [values, setValues] = useState<FormValues>(
    existing ? { ...emptyForm(shape), ...existing.content } : emptyForm(shape),
  );
  const saveMutation = useMutation({
    mutationFn: () =>
      existing
        ? apiClient.editEvalCase(existing.key, values)
        : apiClient.addEvalCase(caseKey.trim(), evalName, values),
    onSuccess: (saved) => {
      refreshEvalCases(queryClient);
      queryClient.setQueryData(queryKeys.evalCase(saved.key), saved);
      if (!existing) {
        router.push(`/admin/evals/cases/${evalName}`);
      }
    },
  });
  const errors = savingErrors(saveMutation.error);
  const isLocked = existing?.archived === true;

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveMutation.mutate();
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-5" noValidate>
      {isLocked ? (
        <p className="m-0 rounded-note border border-line bg-panel px-[18px] py-3 text-[14px] text-text">
          This case is archived: new runs leave it out and it can’t be changed.
          Duplicate it to make a new one like it.
        </p>
      ) : null}
      {existing ? null : (
        <section
          aria-label="Key"
          className="flex flex-col gap-1.5 rounded-card border border-line bg-panel px-6 py-[22px]"
        >
          <label
            htmlFor="case-key"
            className="text-[17px] font-normal text-cream"
          >
            Key
          </label>
          <p id="case-key-description" className={fieldCaption}>
            The case’s stable name, e.g. reminded-of-sister. Runs and the
            terminal pick the case by it, so it can’t change later. Lowercase
            letters, numbers and hyphens; unique across all Evals.
          </p>
          <input
            id="case-key"
            aria-describedby="case-key-description"
            aria-invalid={errors.fields.key !== undefined}
            className={`${inputField} max-w-[420px] font-mono`}
            value={caseKey}
            onChange={(event) => setCaseKey(event.target.value)}
          />
          {errors.fields.key ? (
            <p role="alert" className="m-0 text-[13px] text-danger">
              {errors.fields.key}
            </p>
          ) : null}
        </section>
      )}
      <ShapeFormSections
        shape={shape}
        value={values}
        errors={errors.fields}
        disabled={isLocked}
        onChange={setValues}
      />
      {isLocked ? null : (
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            className={primaryButton}
            disabled={saveMutation.isPending}
          >
            {existing ? "Save case" : "Add case"}
          </button>
          {errors.summary ? (
            <p role="alert" className="m-0 text-[13px] text-danger">
              {errors.summary}
            </p>
          ) : null}
          {saveMutation.isSuccess && existing ? (
            <p role="status" className="m-0 text-[13px] text-soft">
              Saved. The next run uses it; past runs keep the case as it was.
            </p>
          ) : null}
        </div>
      )}
    </form>
  );
}
