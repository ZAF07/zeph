"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CaseResultCard } from "@/components/CaseResultCard";
import { LoadFailed } from "@/components/LoadFailed";
import { ModelCallCard } from "@/components/ModelCallCard";
import { ApiError } from "@/lib/api-client";
import { evalDetails } from "@/lib/evals";
import { formatDuration, formatTokens } from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * One Case Result's full trace: the result, its totals, then every model
 * call its case made, in order, shown as the Model Call Log shows them. The
 * Judge's calls aren't in the trace; its reasons are on the result.
 *
 * @param props - `runId` and `resultId` are the run and the result.
 * @returns The page body, or a loading, not-found or error state.
 */
export function CaseResultTraceView({
  runId,
  resultId,
}: {
  runId: string;
  resultId: string;
}) {
  const apiClient = useApiClient();
  const traceQuery = useQuery({
    queryKey: queryKeys.caseResultTrace(runId, resultId),
    queryFn: () => apiClient.getCaseResultTrace(runId, resultId),
  });
  const trace = traceQuery.data;
  const isNotFound =
    traceQuery.error instanceof ApiError && traceQuery.error.status === 404;

  const backLink = (
    <Link
      href={`/admin/evals/runs/${runId}`}
      className="w-fit text-sm font-medium"
    >
      ← Eval Run
    </Link>
  );

  if (trace === undefined) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        {traceQuery.isPending ? (
          <div
            aria-busy="true"
            aria-label="Loading the trace"
            className="h-[420px] rounded-xl border border-line bg-subtle"
          />
        ) : isNotFound ? (
          <p className="m-0 rounded-card border border-dashed border-line-strong px-6 py-16 text-center text-caption text-ink-muted">
            This Case Result is gone. Its run may have been deleted.
          </p>
        ) : (
          <LoadFailed
            title="Couldn’t load the trace"
            body="The run’s results are still kept."
            onRetry={() => void traceQuery.refetch()}
          />
        )}
      </div>
    );
  }

  const { result, calls } = trace;
  const appTokensIn = calls.reduce((sum, call) => sum + call.tokens_in, 0);
  const appTokensOut = calls.reduce((sum, call) => sum + call.tokens_out, 0);
  const totals = [
    { label: "Model calls", value: String(calls.length) },
    {
      label: "Tokens in calls",
      value: formatTokens(appTokensIn, appTokensOut),
    },
    {
      label: "Time in calls",
      value: formatDuration(
        calls.reduce((sum, call) => sum + call.duration_ms, 0),
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-[22px]">
      {backLink}
      <AdminPageHeader
        title={`Trace of ${result.case_key}`}
        lead={`${evalDetails[result.eval].label} case. Every model call the Companion made for it, with full content. Eval traces never show in the Model Call Log.`}
      />
      <ol className="m-0 list-none p-0">
        <CaseResultCard runId={runId} result={result} />
      </ol>
      <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(min(180px,100%),1fr))] gap-3">
        {totals.map((total) => (
          <div
            key={total.label}
            className="flex flex-col gap-0.5 rounded-card border border-line bg-white px-[18px] py-4"
          >
            <dt className="text-caption text-ink-muted">{total.label}</dt>
            <dd className="m-0 text-[22px] font-normal">{total.value}</dd>
          </div>
        ))}
      </dl>
      <p className="m-0 text-caption text-ink-muted">
        The case’s own tokens also count the Judge, whose calls aren’t listed
        here.
      </p>
      {calls.length > 0 ? (
        calls.map((call) => <ModelCallCard key={call.id} call={call} />)
      ) : (
        <p className="m-0 rounded-card border border-dashed border-line-strong px-6 py-12 text-center text-caption text-ink-muted">
          This case made no model calls.
        </p>
      )}
    </div>
  );
}
