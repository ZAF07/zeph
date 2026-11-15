"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import type { EvalRunPick } from "@/lib/api-client";
import { countOf, describeCost } from "@/lib/evals";
import { formatTokens } from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The estimate of a run's tokens and SGD before it starts, from each case's
 * last run, or a rough figure for cases that have never run. It never blocks
 * starting the run.
 *
 * @param props - `pick` is the whole Evals and single cases the run would run.
 * @returns The estimate, or a line saying it couldn't be worked out.
 */
export function EvalRunEstimateNote({ pick }: { pick: EvalRunPick }) {
  const apiClient = useApiClient();
  const estimateQuery = useQuery({
    queryKey: queryKeys.evalRunEstimate(pick),
    queryFn: () => apiClient.estimateEvalRun(pick),
    placeholderData: keepPreviousData,
  });
  const estimate = estimateQuery.data;

  return (
    <section
      aria-label="Estimate"
      aria-live="polite"
      className="flex flex-col gap-1 rounded-xl border border-line bg-subtle px-[18px] py-3.5"
    >
      <p className="m-0 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted">
        Estimate
      </p>
      {estimate ? (
        <>
          <p className="m-0">
            About {formatTokens(estimate.tokens_in, estimate.tokens_out)} tokens
            · {describeCost(estimate)}
          </p>
          <p className="m-0 text-caption text-ink-muted">
            From each case’s last run, at DeepSeek’s peak price, so the real
            cost is usually the same or lower.
            {estimate.rough_case_count > 0
              ? ` ${countOf(estimate.rough_case_count, "case")} never ran, so ${
                  estimate.rough_case_count === 1 ? "its" : "their"
                } figure is rough.`
              : ""}
          </p>
        </>
      ) : estimateQuery.isError ? (
        <p className="m-0 text-caption text-ink-muted">
          Couldn’t work out an estimate. You can still start the run.
        </p>
      ) : (
        <p className="m-0 text-caption text-ink-muted">Working it out…</p>
      )}
    </section>
  );
}
