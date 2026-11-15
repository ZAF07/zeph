"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { EvalPill } from "@/components/EvalPill";
import { LoadFailed } from "@/components/LoadFailed";
import { CaseResultCard } from "@/components/CaseResultCard";
import type { EvalRunDetails } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import {
  describeEvals,
  describeTotals,
  isRunGoing,
  runStateLabels,
} from "@/lib/evals";
import { formatTokens } from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/** How often the page checks a Queued or Running run again. */
export const runCheckMilliseconds = 2000;

/**
 * Says how far a run has got, for the line under its title.
 *
 * @param run - The run.
 * @returns E.g. "Waiting for the runner" or "4 of 30 cases done".
 */
function progressText(run: EvalRunDetails): string {
  const done = run.results.length;
  if (run.state === "queued") {
    return "Waiting for the runner. It starts once any run before it ends.";
  }
  if (run.case_count === null) {
    return `${done} cases done`;
  }
  return `${done} of ${run.case_count} cases done`;
}

/**
 * The page of one Eval Run: its state, who started it and its totals, then
 * each Case Result as it finishes. It checks again every two seconds while
 * the run is Queued or Running, and stops once the run has ended.
 *
 * @param props - `runId` is the run's ID.
 * @returns The run, or a loading or error state.
 */
export function EvalRunView({ runId }: { runId: string }) {
  const apiClient = useApiClient();
  const runQuery = useQuery({
    queryKey: queryKeys.evalRun(runId),
    queryFn: () => apiClient.getEvalRun(runId),
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state === undefined || isRunGoing(state)
        ? runCheckMilliseconds
        : false;
    },
  });
  const run = runQuery.data;

  if (run === undefined) {
    return runQuery.isError ? (
      <LoadFailed
        title="Couldn’t load this Eval Run"
        body="If it is running, it keeps going."
        onRetry={() => void runQuery.refetch()}
      />
    ) : (
      <div
        aria-busy="true"
        aria-label="Loading run"
        className="h-[320px] rounded-xl border border-line bg-subtle"
      />
    );
  }

  const startedBy =
    run.started_from === "terminal"
      ? "from the terminal"
      : `by ${run.started_by_name ?? "an Admin"} on the Dashboard`;

  return (
    <div className="flex flex-col gap-[22px]">
      <header className="flex flex-col gap-2">
        <Link href="/admin/evals" className="text-caption text-ink-muted">
          ← Eval Runs
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="m-0 text-h1 font-normal">
            {describeEvals(run.evals)}
          </h1>
          <EvalPill {...runStateLabels[run.state]} />
        </div>
        <p className="m-0 text-body text-ink-soft">
          Started {startedBy}, {formatSavedAt(run.queued_at)}.
        </p>
      </header>

      <div className="flex flex-wrap gap-x-8 gap-y-2 rounded-xl border border-line bg-white px-[18px] py-3.5">
        <p className="m-0" aria-live="polite">
          {progressText(run)}
        </p>
        <p className="m-0">{describeTotals(run)}</p>
        <p className="m-0 text-ink-muted">
          {formatTokens(run.tokens_in, run.tokens_out)}
        </p>
      </div>
      {run.errored > 0 ? (
        <p className="m-0 text-caption text-ink-muted">
          Errors are cases that couldn’t be checked, such as the model not
          answering. They don’t count as fails.
        </p>
      ) : null}
      {run.state === "interrupted" ? (
        <p className="m-0 text-caption text-ink-muted">
          The runner stopped during this run, so it ended early. It isn’t
          started again by itself, since runs cost money.
        </p>
      ) : null}

      {run.results.length > 0 ? (
        <ol className="m-0 flex list-none flex-col gap-2.5 p-0">
          {run.results.map((result) => (
            <CaseResultCard key={result.id} result={result} />
          ))}
        </ol>
      ) : (
        <div className="rounded-card border border-dashed border-line-strong px-6 py-12 text-center text-caption text-ink-muted">
          Case Results appear here as each case finishes.
        </div>
      )}
    </div>
  );
}
