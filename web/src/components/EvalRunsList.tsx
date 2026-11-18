"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { EmptyState } from "@/components/EmptyState";
import { EvalPill } from "@/components/EvalPill";
import { LoadFailed } from "@/components/LoadFailed";
import { formatSavedAt } from "@/lib/dates";
import {
  describeCost,
  describeEvals,
  describeTotals,
  runStateLabels,
} from "@/lib/evals";
import { formatTokens } from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const headings = [
  "When",
  "Started by",
  "Evals",
  "State",
  "Results",
  "Tokens and cost",
];

const cell = "px-[18px] py-3.5";

/**
 * The Eval Runs list, newest first, with a button to start a new run. Runs
 * started from the terminal (`make eval`) are hidden until "Show terminal
 * runs" is on, since they are mostly development and agents.
 *
 * @returns The toolbar and table, or a loading, empty or error state.
 */
export function EvalRunsList() {
  const apiClient = useApiClient();
  const [includeTerminal, setIncludeTerminal] = useState(false);
  const runsQuery = useQuery({
    queryKey: queryKeys.evalRuns(includeTerminal),
    queryFn: () => apiClient.listEvalRuns(includeTerminal),
  });
  const runs = runsQuery.data;

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <button
          type="button"
          aria-pressed={includeTerminal}
          onClick={() => setIncludeTerminal(!includeTerminal)}
          className={`min-h-10 cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium ${
            includeTerminal
              ? "border-ink bg-ink text-white"
              : "border-line-strong bg-transparent text-ink-body"
          }`}
        >
          Show terminal runs
        </button>
        <Link href="/admin/evals/new" className={primaryButton}>
          New run
        </Link>
      </div>

      {runsQuery.isPending ? (
        <div
          aria-busy="true"
          aria-label="Loading runs"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {runs === undefined && runsQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Eval Runs"
          body="Runs already started keep going."
          onRetry={() => void runsQuery.refetch()}
        />
      ) : null}

      {runs !== undefined && runs.length === 0 ? (
        <EmptyState
          title="No Eval Runs yet"
          body="Start a run to check how the Companion behaves with the real model. Runs cost money: each case calls DeepSeek."
        />
      ) : null}

      {runs !== undefined && runs.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="w-full min-w-[820px] border-collapse text-sm">
            <thead>
              <tr>
                {headings.map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className="whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 text-left font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="border-b border-line last:border-b-0"
                >
                  <td className={`${cell} whitespace-nowrap`}>
                    <Link
                      href={`/admin/evals/runs/${run.id}`}
                      className="font-medium"
                    >
                      {formatSavedAt(run.queued_at)}
                    </Link>
                  </td>
                  <td className={cell}>
                    {run.started_from === "terminal"
                      ? "Terminal"
                      : (run.started_by_name ?? "Unknown Admin")}
                  </td>
                  <td className={cell}>{describeEvals(run.evals)}</td>
                  <td className={cell}>
                    <EvalPill {...runStateLabels[run.state]} />
                  </td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {describeTotals(run)}
                  </td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {formatTokens(run.tokens_in, run.tokens_out)}
                    <span className="block text-caption text-ink-muted">
                      {describeCost(run)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
