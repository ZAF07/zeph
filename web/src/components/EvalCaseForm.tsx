"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { keyInputField } from "@/components/form-styles";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
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
 * @param props - `evalName` is its Eval, `shape` its case shape,
 *   `existing` the case being edited, or undefined for a new one, and
 *   `draft` the key and content a new case's form starts with.
 * @returns The form.
 */
export function EvalCaseForm({
  evalName,
  shape,
  existing,
  draft,
}: {
  evalName: EvalName;
  shape: FormShape;
  existing?: EvalCase;
  draft?: { key: string; content: FormValues };
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [caseKey, setCaseKey] = useState(existing?.key ?? draft?.key ?? "");
  const [values, setValues] = useState<FormValues>({
    ...emptyForm(shape),
    ...(existing?.content ?? draft?.content),
  });
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
    <form onSubmit={save} className="flex flex-col gap-6" noValidate>
      {isLocked ? (
        <p className="m-0 rounded-note border border-line bg-panel px-[18px] py-3 text-[14px] text-text">
          This case is archived: new runs leave it out and it can’t be changed.
          Duplicate it to make a new one like it.
        </p>
      ) : null}
      {existing ? null : (
        <section
          aria-label="Key"
          className="box-border flex flex-col gap-[14px] rounded-card border border-line bg-panel px-6 py-[22px]"
        >
          <div>
            <h2 className="m-0 text-[17px] font-normal text-cream">
              <label htmlFor="case-key">Key</label>
            </h2>
            <p
              id="case-key-description"
              className="mt-1 mb-0 max-w-[640px] text-[13px] text-soft"
            >
              The case’s stable name, e.g. guilt-and-job-worry. Runs and the
              terminal pick the case by it, so it can’t change later. Lowercase
              letters, numbers and hyphens; unique across all Evals.
            </p>
          </div>
          <input
            id="case-key"
            aria-describedby="case-key-description"
            aria-invalid={errors.fields.key !== undefined}
            className={keyInputField}
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
            <SaveFailedNote>{errors.summary}</SaveFailedNote>
          ) : null}
          {saveMutation.isSuccess && existing ? (
            <SavedNote>
              Saved. The next run uses it; past runs keep the case as it was.
            </SavedNote>
          ) : null}
        </div>
      )}
    </form>
  );
}
