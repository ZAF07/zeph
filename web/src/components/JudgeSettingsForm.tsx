"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { ShapeFormSections } from "@/components/ShapeFormSections";
import type { FormValues, JudgeSettings } from "@/lib/api-client";
import { savingErrors } from "@/lib/eval-forms";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Judge's model, thinking and prompts, in the same form style as Eval
 * Cases. A save applies from the next run; past runs keep the Judge they
 * used.
 *
 * @param props - `settings` holds the form's shape and current values.
 * @returns The form.
 */
export function JudgeSettingsForm({ settings }: { settings: JudgeSettings }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [values, setValues] = useState<FormValues>(settings.values);
  const saveMutation = useMutation({
    mutationFn: () => apiClient.saveJudgeSettings(values),
    onSuccess: (saved) => {
      queryClient.setQueryData(queryKeys.judgeSettings, saved);
    },
  });
  const errors = savingErrors(saveMutation.error);

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveMutation.mutate();
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-5" noValidate>
      <ShapeFormSections
        shape={settings.shape}
        value={values}
        errors={errors.fields}
        disabled={false}
        onChange={setValues}
      />
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          className={primaryButton}
          disabled={saveMutation.isPending}
        >
          Save Judge
        </button>
        {errors.summary ? (
          <p role="alert" className="m-0 text-[13px] text-danger">
            {errors.summary}
          </p>
        ) : null}
        {saveMutation.isSuccess ? (
          <p role="status" className="m-0 text-[13px] text-soft">
            Saved. The next run uses it.
          </p>
        ) : null}
      </div>
    </form>
  );
}
