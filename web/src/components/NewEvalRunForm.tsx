"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import type { EvalName } from "@/lib/api-client";
import { evalDetails, evalOrder } from "@/lib/evals";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The New run form: tick whole Evals, see how many cases each runs, then
 * start the run and open its page. The run waits as Queued while another is
 * running.
 *
 * @returns The form, or a loading or error state.
 */
export function NewEvalRunForm() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [chosen, setChosen] = useState<EvalName[]>([]);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const evalsQuery = useQuery({
    queryKey: queryKeys.evals,
    queryFn: () => apiClient.listEvals(),
  });
  const evals = evalsQuery.data;

  function toggle(name: EvalName) {
    setChosen(
      chosen.includes(name)
        ? chosen.filter((other) => other !== name)
        : [...chosen, name],
    );
  }

  async function start(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStarting(true);
    setError(null);
    try {
      const run = await apiClient.startEvalRun(
        evalOrder.filter((name) => chosen.includes(name)),
      );
      void queryClient.invalidateQueries({ queryKey: ["eval-runs"] });
      router.push(`/admin/evals/runs/${run.id}`);
    } catch {
      setError("Couldn’t start the run. Try again.");
      setStarting(false);
    }
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

  const caseCount = evals
    .filter((summary) => chosen.includes(summary.eval))
    .reduce((count, summary) => count + summary.case_keys.length, 0);

  return (
    <form
      onSubmit={(event) => void start(event)}
      className="flex flex-col gap-5"
    >
      <fieldset className="m-0 flex flex-col gap-2.5 border-0 p-0">
        <legend className="mb-2.5 text-body font-medium">Evals to run</legend>
        {evals.map((summary) => {
          const details = evalDetails[summary.eval];
          const count = summary.case_keys.length;
          return (
            <div
              key={summary.eval}
              className="flex flex-col gap-1.5 rounded-xl border border-line bg-white px-[18px] py-3.5"
            >
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 size-4"
                  checked={chosen.includes(summary.eval)}
                  disabled={count === 0}
                  onChange={() => toggle(summary.eval)}
                />
                <span className="flex flex-col gap-0.5">
                  <span className="font-medium">
                    {details.label}{" "}
                    <span className="font-normal text-ink-muted">
                      · {count === 1 ? "1 case" : `${count} cases`}
                    </span>
                  </span>
                  <span className="text-caption text-ink-soft">
                    {details.checks}
                  </span>
                </span>
              </label>
              {count > 0 ? (
                <details className="ml-7 text-caption text-ink-muted">
                  <summary className="cursor-pointer">Cases</summary>
                  <p className="m-0 mt-1.5 font-mono text-xs leading-relaxed">
                    {summary.case_keys.join(", ")}
                  </p>
                </details>
              ) : null}
            </div>
          );
        })}
      </fieldset>
      <p className="m-0 text-caption text-ink-muted">
        Each case calls DeepSeek, so a run costs money. Cases are read-only for
        now.
      </p>
      {error ? (
        <p role="alert" className="m-0 text-caption text-danger">
          {error}
        </p>
      ) : null}
      <div>
        <button
          type="submit"
          className={primaryButton}
          disabled={chosen.length === 0 || starting}
        >
          {chosen.length === 0
            ? "Start run"
            : `Start run · ${caseCount === 1 ? "1 case" : `${caseCount} cases`}`}
        </button>
      </div>
    </form>
  );
}
