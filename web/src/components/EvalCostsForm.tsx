"use client";

import { useQuery } from "@tanstack/react-query";

import { EvalCostsFields } from "@/components/EvalCostsFields";
import { LoadFailed } from "@/components/LoadFailed";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Model Prices and Eval run token limit form. Both are Platform
 * Settings, saved together.
 *
 * @returns The form, or a loading or error state.
 */
export function EvalCostsForm() {
  const apiClient = useApiClient();
  const costsQuery = useQuery({
    queryKey: queryKeys.evalCosts,
    queryFn: () => apiClient.getEvalCosts(),
  });
  const costs = costsQuery.data;

  if (costs === undefined) {
    return costsQuery.isError ? (
      <LoadFailed
        title="Couldn’t load the Model Prices"
        body="Runs still use the saved prices."
        onRetry={() => void costsQuery.refetch()}
      />
    ) : (
      <div
        aria-busy="true"
        aria-label="Loading Model Prices"
        className="h-[320px] rounded-xl border border-line bg-subtle"
      />
    );
  }
  return <EvalCostsFields costs={costs} />;
}
