"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { EvalPill } from "@/components/EvalPill";
import { EvalRunActions } from "@/components/EvalRunActions";
import { EvalRunGrid } from "@/components/EvalRunGrid";
import { EvalRunSnapshotDetails } from "@/components/EvalRunSnapshotDetails";
import { EvalVariantsPanel } from "@/components/EvalVariantsPanel";
import { cardLink } from "@/components/card-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import type { EvalRunDetails } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import {
  countOf,
  describeCost,
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
  return `${done} of ${countOf(run.case_count, "case")} done`;
}

/**
 * The page of one Eval Run: its state, who started it, its running totals
 * (passes, tokens and SGD), what an Admin can do with it, its Variants with
 * Make Live, what it used, then the grid of Case Results as they finish, a
 * row per case and a column per Variant. It checks again every two seconds
 * while the run is Queued or Running, and stops once the run has ended.
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
      return state !== undefined && isRunGoing(state)
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
      <LoadingPanel shape="card" label="Loading run" />
    );
  }

  const startedBy =
    run.started_from === "terminal"
      ? "from the terminal"
      : `by ${run.started_by_name ?? "an Admin"} on the Dashboard`;

  return (
    <div className="flex flex-col gap-[22px]">
      <header className="flex flex-col gap-2">
        <Link href="/admin/evals" className={`${cardLink} w-fit`}>
          ← Eval Runs
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="m-0 text-[32px] leading-[1.15] font-normal text-cream">
            {describeEvals(run.evals)}
          </h1>
          <EvalPill {...runStateLabels[run.state]} />
        </div>
        <p className="m-0 text-[14px] text-soft">
          Started {startedBy}, {formatSavedAt(run.queued_at)}.
          {run.rerun_of ? (
            <>
              {" "}
              Re-runs the failed cases of{" "}
              <Link
                href={`/admin/evals/runs/${run.rerun_of}`}
                className="underline"
              >
                an earlier run
              </Link>
              .
            </>
          ) : null}
        </p>
      </header>

      <EvalRunActions run={run} />

      <div className="flex flex-wrap gap-x-8 gap-y-2 rounded-card border border-line bg-panel px-[18px] py-3.5 text-[14px] text-text">
        <p className="m-0" aria-live="polite">
          {progressText(run)}
        </p>
        <p className="m-0">{describeTotals(run)}</p>
        <p className="m-0 text-soft">
          {formatTokens(run.tokens_in, run.tokens_out)}
        </p>
        <p className="m-0 text-soft">{describeCost(run)}</p>
      </div>
      {run.errored > 0 ? (
        <p className="m-0 text-[13px] text-soft">
          Errors are cases that couldn’t be checked, such as the model not
          answering. They don’t count as fails.
        </p>
      ) : null}
      {run.cancel_requested && isRunGoing(run.state) ? (
        <p className="m-0 text-[13px] text-soft">
          Cancelling. The run stops after the case it is on, keeping every
          finished case.
        </p>
      ) : null}
      {run.state === "cancelled" ? (
        <p className="m-0 text-[13px] text-soft">
          An Admin cancelled this run. The cases finished before it stopped are
          kept.
        </p>
      ) : null}
      {run.state === "stopped_over_limit" ? (
        <p className="m-0 text-[13px] text-soft">
          This run went over its token limit
          {run.token_limit !== null
            ? ` of ${run.token_limit.toLocaleString("en")}`
            : ""}{" "}
          and stopped by itself. The limit is set on{" "}
          <Link href="/admin/evals/costs" className="underline">
            Model Prices
          </Link>
          .
        </p>
      ) : null}
      {run.state === "interrupted" ? (
        <p className="m-0 text-[13px] text-soft">
          The runner stopped during this run, so it ended early. It isn’t
          started again by itself, since runs cost money.
        </p>
      ) : null}

      <EvalVariantsPanel run={run} />

      <EvalRunSnapshotDetails runId={run.id} />

      {run.results.length > 0 ? (
        <EvalRunGrid run={run} />
      ) : (
        <div className="rounded-card border border-dashed border-line-strong px-6 py-[22px] text-[14px] text-soft">
          Case Results appear here as each case finishes.
        </div>
      )}
    </div>
  );
}
