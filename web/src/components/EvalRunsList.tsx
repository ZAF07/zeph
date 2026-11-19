"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { DataTable } from "@/components/DataTable";
import { FilterToggle } from "@/components/FilterToggle";
import { LoadFailed } from "@/components/LoadFailed";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import type { EvalRun, EvalRunState } from "@/lib/api-client";
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

const finishedStates: EvalRunState[] = ["finished"];
const failedStates: EvalRunState[] = ["stopped_over_limit", "interrupted"];

const columns: TableColumn<EvalRun>[] = [
  {
    heading: "When",
    isMain: true,
    cell: (run) => (
      <Link
        href={`/admin/evals/runs/${run.id}`}
        className="whitespace-nowrap text-text underline"
      >
        {formatSavedAt(run.queued_at)}
      </Link>
    ),
  },
  {
    heading: "Started by",
    isMain: true,
    cell: (run) =>
      run.started_from === "terminal"
        ? "Terminal"
        : (run.started_by_name ?? "Unknown Admin"),
  },
  { heading: "Evals", cell: (run) => describeEvals(run.evals) },
  {
    heading: "State",
    cell: (run) => (
      <StatusPill
        filled={finishedStates.includes(run.state)}
        danger={failedStates.includes(run.state)}
      >
        {runStateLabels[run.state].label}
      </StatusPill>
    ),
  },
  { heading: "Results", cell: (run) => describeTotals(run) },
  {
    heading: "Tokens and cost",
    cell: (run) => (
      <>
        {formatTokens(run.tokens_in, run.tokens_out)}
        <span className="block text-[12px] text-soft">{describeCost(run)}</span>
      </>
    ),
  },
];

/**
 * The Eval Runs list, newest first, with a button to start a new run. Runs
 * started from the terminal (`make eval`) are hidden until "Show terminal
 * runs" is on, since they are mostly development and agents. Built from the
 * admin table template.
 *
 * @returns The filters and table, or a loading, empty or error state in
 *   place of the table.
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
      <div className="flex flex-wrap items-center gap-2.5">
        <FilterToggle
          label="Show terminal runs"
          on={includeTerminal}
          onChange={setIncludeTerminal}
        />
        <Link href="/admin/evals/new" className={primaryButton}>
          New run
        </Link>
      </div>

      {runsQuery.isPending ? <TableLoading label="Loading runs" /> : null}

      {runs === undefined && runsQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Eval Runs"
          body="Runs already started keep going."
          onRetry={() => void runsQuery.refetch()}
        />
      ) : null}

      {runs !== undefined && runs.length === 0 ? (
        <TableEmpty
          title="No Eval Runs yet"
          body="Start a run to check how the Companion behaves with the real model. Runs cost money: each case calls DeepSeek."
        />
      ) : null}

      {runs !== undefined && runs.length > 0 ? (
        <DataTable
          columns={columns}
          rows={runs}
          rowKey={(run) => run.id}
          minWidthClass="min-w-[820px]"
        />
      ) : null}
    </>
  );
}
