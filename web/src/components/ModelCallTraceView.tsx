"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { cardLink } from "@/components/card-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { StatTiles } from "@/components/StatTiles";
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
    <Link href={logPath} className={`${cardLink} w-fit`}>
      ← Model call log
    </Link>
  );

  if (traceQuery.isPending) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <LoadingPanel shape="card" label="Loading the trace" />
      </div>
    );
  }

  if (!trace && isNotFound) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <div className="box-border rounded-card border border-dashed border-line-strong px-6 py-[22px]">
          <h1 className="m-0 text-[16px] font-normal text-cream">
            This trace is gone
          </h1>
          <p className="mt-1.5 mb-0 text-[14px] text-soft">
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
      <StatTiles tiles={totals} />
      {trace.calls.map((call) => (
        <ModelCallCard key={call.id} call={call} />
      ))}
    </div>
  );
}
