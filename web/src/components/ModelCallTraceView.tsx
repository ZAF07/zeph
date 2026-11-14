"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { LoadFailed } from "@/components/LoadFailed";
import { ModelCallCard } from "@/components/ModelCallCard";
import { ApiError } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import {
  formatDuration,
  formatTokens,
  traceKindLabel,
} from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const logPath = "/admin/model-calls";

/**
 * One Model Call Log trace: what it was for, who and when, its totals, then
 * every model call in it, in order.
 *
 * @param props - `traceId` is the trace to show.
 * @returns The page body, or a loading, not-found or error state.
 */
export function ModelCallTraceView({ traceId }: { traceId: string }) {
  const apiClient = useApiClient();
  const traceQuery = useQuery({
    queryKey: queryKeys.modelCallTrace(traceId),
    queryFn: () => apiClient.getModelCallTrace(traceId),
  });
  const trace = traceQuery.data;
  const isNotFound =
    traceQuery.error instanceof ApiError && traceQuery.error.status === 404;

  const backLink = (
    <Link href={logPath} className="w-fit text-sm font-medium">
      ← Model call log
    </Link>
  );

  if (traceQuery.isPending) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <div
          aria-busy="true"
          aria-label="Loading the trace"
          className="h-[420px] rounded-xl border border-line bg-subtle"
        />
      </div>
    );
  }

  if (!trace && isNotFound) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <h1 className="m-0 text-[22px] font-medium tracking-[-0.02em]">
            This trace is gone
          </h1>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            It was removed with the User’s messages, by Message Retention or
            when they deleted their data.
          </p>
        </div>
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <LoadFailed
          title="Couldn’t load the trace"
          body="The Companion is still replying as normal."
          onRetry={() => void traceQuery.refetch()}
        />
      </div>
    );
  }

  const who = trace.user_name ?? trace.user_email ?? "Unknown User";
  const totals = [
    {
      label: "Tokens",
      value: formatTokens(trace.tokens_in, trace.tokens_out),
    },
    { label: "Time taken", value: formatDuration(trace.duration_ms) },
    { label: "Model calls", value: String(trace.calls.length) },
    { label: "Errors", value: String(trace.error_count) },
  ];

  return (
    <div className="flex flex-col gap-[22px]">
      {backLink}
      <AdminPageHeader
        title={`${traceKindLabel(trace.kind)} for ${who}`}
        lead={`Started ${formatSavedAt(trace.started_at)}.`}
      />
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
      {trace.calls.map((call) => (
        <ModelCallCard key={call.id} call={call} />
      ))}
    </div>
  );
}
