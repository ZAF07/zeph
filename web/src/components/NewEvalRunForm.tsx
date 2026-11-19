"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { EvalRunEstimateNote } from "@/components/EvalRunEstimateNote";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { VariantOverridesEditor } from "@/components/VariantOverridesEditor";
import {
  ApiError,
  type EvalName,
  type EvalRunPick,
  type EvalRunRequest,
  type EvalSummary,
  type SettingOverrides,
} from "@/lib/api-client";
import { countOf, evalDetails, evalOrder } from "@/lib/evals";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * Works out which cases a pick runs: every case of a whole Eval, plus the
 * single cases ticked in other Evals.
 *
 * @param evals - Every Eval with its cases.
 * @param pick - The whole Evals and single cases ticked.
 * @returns The keys of the cases the run would run.
 */
function pickedCaseKeys(evals: EvalSummary[], pick: EvalRunPick): string[] {
  return evals.flatMap((summary) =>
    pick.evals.includes(summary.eval)
      ? summary.case_keys
      : summary.case_keys.filter((key) => pick.case_keys.includes(key)),
  );
}

/** The letters of a run's Variants, in order; a run has one to three. */
const variantLetters = ["A", "B", "C"];

/** How many times each case can run per Variant. */
const repeatChoices = [1, 2, 3, 4, 5];

/**
 * The New run form: tick whole Evals or single cases inside them, add up to
 * three Variants with their own Setting Overrides, pick the Repeats, see an
 * estimate of the run's tokens and SGD, then start it and open its page. The
 * run waits as Queued while another is running.
 *
 * @returns The form, or a loading or error state.
 */
export function NewEvalRunForm() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [wholeEvals, setWholeEvals] = useState<EvalName[]>([]);
  const [singleCases, setSingleCases] = useState<string[]>([]);
  const [variants, setVariants] = useState<SettingOverrides[]>([{}]);
  const [repeats, setRepeats] = useState(1);
  const choicesQuery = useQuery({
    queryKey: queryKeys.settingOverrideChoices,
    queryFn: () => apiClient.listSettingOverrideChoices(),
  });
  const choices = choicesQuery.data;
  const evalsQuery = useQuery({
    queryKey: queryKeys.evals,
    queryFn: () => apiClient.listEvals(),
  });
  const evals = evalsQuery.data;
  const startMutation = useMutation({
    mutationFn: (runRequest: EvalRunRequest) =>
      apiClient.startEvalRun(runRequest),
    onSuccess: (run) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.allEvalRuns });
      router.push(`/admin/evals/runs/${run.id}`);
    },
  });

  const caseEval = new Map(
    (evals ?? []).flatMap((summary) =>
      summary.case_keys.map((key) => [key, summary.eval] as const),
    ),
  );
  const pick: EvalRunPick = {
    evals: evalOrder.filter((name) => wholeEvals.includes(name)),
    case_keys: singleCases.filter((key) => {
      const name = caseEval.get(key);
      return name !== undefined && !wholeEvals.includes(name);
    }),
  };
  const pickedCount = evals ? pickedCaseKeys(evals, pick).length : 0;
  const caseCount = pickedCount * variants.length * repeats;
  const runRequest: EvalRunRequest = { ...pick, variants, repeats };
  const refusal =
    startMutation.error instanceof ApiError ? startMutation.error.detail : null;

  function changeVariant(index: number, overrides: SettingOverrides) {
    setVariants(
      variants.map((other, at) => (at === index ? overrides : other)),
    );
    startMutation.reset();
  }

  function toggleEval(name: EvalName) {
    setWholeEvals(
      wholeEvals.includes(name)
        ? wholeEvals.filter((other) => other !== name)
        : [...wholeEvals, name],
    );
  }

  function toggleCase(key: string) {
    setSingleCases(
      singleCases.includes(key)
        ? singleCases.filter((other) => other !== key)
        : [...singleCases, key],
    );
  }

  function start(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startMutation.mutate(runRequest);
  }

  if (evals === undefined) {
    return evalsQuery.isError ? (
      <LoadFailed
        title="Couldn’t load the Evals"
        body="No run was started."
        onRetry={() => void evalsQuery.refetch()}
      />
    ) : (
      <LoadingPanel shape="card" label="Loading Evals" />
    );
  }

  return (
    <form onSubmit={start} className="flex flex-col gap-5">
      <fieldset className="m-0 flex flex-col gap-2.5 border-0 p-0">
        <legend className="mb-2.5 text-[15px] font-normal text-text">
          Evals to run
        </legend>
        {evals.map((summary) => {
          const details = evalDetails[summary.eval];
          const count = summary.case_keys.length;
          const isWhole = wholeEvals.includes(summary.eval);
          const singleCount = summary.case_keys.filter((key) =>
            singleCases.includes(key),
          ).length;
          return (
            <div
              key={summary.eval}
              className="flex flex-col gap-1.5 rounded-card border border-line bg-panel px-[18px] py-3.5 text-[14px] text-text"
            >
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 size-4 accent-cream"
                  checked={isWhole}
                  disabled={count === 0}
                  onChange={() => toggleEval(summary.eval)}
                />
                <span className="flex flex-col gap-0.5">
                  <span className="text-[15px] text-cream">
                    {details.label}{" "}
                    <span className="text-soft">
                      · {countOf(count, "case")}
                    </span>
                  </span>
                  <span className="text-[13px] text-soft">
                    {details.checks}
                  </span>
                </span>
              </label>
              {count > 0 ? (
                <details className="ml-7 text-[13px] text-soft">
                  <summary className="cursor-pointer">
                    {isWhole
                      ? "Cases"
                      : singleCount > 0
                        ? `Single cases · ${singleCount} picked`
                        : "Pick single cases"}
                  </summary>
                  <ul className="m-0 mt-1.5 flex list-none flex-col gap-1 p-0">
                    {summary.case_keys.map((key) => (
                      <li key={key}>
                        <label className="flex min-h-11 cursor-pointer items-center gap-2 font-mono text-[12px] text-text">
                          <input
                            type="checkbox"
                            className="size-3.5 accent-cream"
                            checked={isWhole || singleCases.includes(key)}
                            disabled={isWhole}
                            onChange={() => toggleCase(key)}
                          />
                          {key}
                        </label>
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </div>
          );
        })}
      </fieldset>
      <fieldset className="m-0 flex flex-col gap-2.5 border-0 p-0">
        <legend className="mb-1 text-[15px] font-normal text-text">
          Variants
        </legend>
        <p className={`${fieldCaption} mb-1.5`}>
          Each Variant runs the same cases, side by side. A runs the live
          settings unless you change some; add B or C to try other settings.
          Changes apply to this run only and never touch the live settings.
        </p>
        {choices ? (
          variants.map((overrides, index) => (
            <VariantOverridesEditor
              key={variantLetters[index]}
              letter={variantLetters[index] ?? ""}
              overrides={overrides}
              choices={choices}
              onChange={(changed) => changeVariant(index, changed)}
              onRemove={
                index > 0 && index === variants.length - 1
                  ? () => setVariants(variants.slice(0, -1))
                  : undefined
              }
            />
          ))
        ) : choicesQuery.isError ? (
          <p className="m-0 text-[13px] text-danger">
            Couldn’t load the settings to change. The run can still use the live
            settings.
          </p>
        ) : (
          <LoadingPanel shape="card" label="Loading settings" />
        )}
        {choices && variants.length < variantLetters.length ? (
          <div>
            <button
              type="button"
              className={secondaryButton}
              onClick={() => setVariants([...variants, {}])}
            >
              Add Variant {variantLetters[variants.length]}
            </button>
          </div>
        ) : null}
      </fieldset>
      <label className={`${fieldLabel} max-w-[320px]`}>
        Repeats
        <select
          className={inputField}
          value={repeats}
          onChange={(event) => setRepeats(Number(event.target.value))}
        >
          {repeatChoices.map((count) => (
            <option key={count} value={count}>
              {count === 1 ? "Once" : `${count} times`}
            </option>
          ))}
        </select>
        <span className={fieldCaption}>
          How many times each case runs per Variant, to tell a steady result
          from luck.
        </span>
      </label>
      {caseCount > 0 ? (
        <EvalRunEstimateNote runRequest={runRequest} />
      ) : (
        <p className="m-0 text-[13px] text-soft">
          Each case calls DeepSeek, so a run costs money. Pick Evals or cases to
          see an estimate.
        </p>
      )}
      <p className="m-0 text-[13px] text-soft">
        Cases are run as they are now; edit them under Cases.
      </p>
      {startMutation.isError ? (
        <SaveFailedNote>
          {refusal
            ? `Couldn’t start the run: ${refusal}`
            : "Couldn’t start the run. Try again."}
        </SaveFailedNote>
      ) : null}
      <div>
        <button
          type="submit"
          className={primaryButton}
          disabled={
            caseCount === 0 ||
            startMutation.isPending ||
            startMutation.isSuccess
          }
        >
          {caseCount === 0
            ? "Start run"
            : `Start run · ${countOf(caseCount, "case")}`}
        </button>
      </div>
    </form>
  );
}
