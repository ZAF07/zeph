"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { EvalRunEstimateNote } from "@/components/EvalRunEstimateNote";
import { LoadFailed } from "@/components/LoadFailed";
import type { EvalName, EvalRunPick, EvalSummary } from "@/lib/api-client";
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

/**
 * The New run form: tick whole Evals or single cases inside them, see an
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
  const evalsQuery = useQuery({
    queryKey: queryKeys.evals,
    queryFn: () => apiClient.listEvals(),
  });
  const evals = evalsQuery.data;
  const startMutation = useMutation({
    mutationFn: (pick: EvalRunPick) => apiClient.startEvalRun(pick),
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
  const caseCount = evals ? pickedCaseKeys(evals, pick).length : 0;

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
    startMutation.mutate(pick);
  }

  if (evals === undefined) {
    return evalsQuery.isError ? (
      <LoadFailed
        title="Couldn’t load the Evals"
        body="No run was started."
        onRetry={() => void evalsQuery.refetch()}
      />
    ) : (
      <div
        aria-busy="true"
        aria-label="Loading Evals"
        className="h-[320px] rounded-xl border border-line bg-subtle"
      />
    );
  }

  return (
    <form onSubmit={start} className="flex flex-col gap-5">
      <fieldset className="m-0 flex flex-col gap-2.5 border-0 p-0">
        <legend className="mb-2.5 text-body font-medium">Evals to run</legend>
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
              className="flex flex-col gap-1.5 rounded-xl border border-line bg-white px-[18px] py-3.5"
            >
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 size-4"
                  checked={isWhole}
                  disabled={count === 0}
                  onChange={() => toggleEval(summary.eval)}
                />
                <span className="flex flex-col gap-0.5">
                  <span className="font-medium">
                    {details.label}{" "}
                    <span className="font-normal text-ink-muted">
                      · {countOf(count, "case")}
                    </span>
                  </span>
                  <span className="text-caption text-ink-soft">
                    {details.checks}
                  </span>
                </span>
              </label>
              {count > 0 ? (
                <details className="ml-7 text-caption text-ink-muted">
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
                        <label className="flex cursor-pointer items-center gap-2 font-mono text-xs">
                          <input
                            type="checkbox"
                            className="size-3.5"
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
      {caseCount > 0 ? (
        <EvalRunEstimateNote pick={pick} />
      ) : (
        <p className="m-0 text-caption text-ink-muted">
          Each case calls DeepSeek, so a run costs money. Pick Evals or cases to
          see an estimate.
        </p>
      )}
      <p className="m-0 text-caption text-ink-muted">
        Cases are run as they are now; edit them under Cases.
      </p>
      {startMutation.isError ? (
        <p role="alert" className="m-0 text-caption text-danger">
          Couldn’t start the run. Try again.
        </p>
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
