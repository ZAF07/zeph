"use client";

import { useQuery } from "@tanstack/react-query";

import { EvalCaseForm } from "@/components/EvalCaseForm";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import type { EvalName } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * Loads what a case form needs, its Eval's case shape and, when editing,
 * the case, then shows the form.
 *
 * @param props - `evalName` is the case's Eval; `caseKey` is the case to
 *   edit, or undefined to add a new one.
 * @returns The form, or a loading or error state.
 */
export function EvalCaseEditor({
  evalName,
  caseKey,
}: {
  evalName: EvalName;
  caseKey?: string;
}) {
  const apiClient = useApiClient();
  const shapesQuery = useQuery({
    queryKey: queryKeys.evalCaseShapes,
    queryFn: () => apiClient.listEvalCaseShapes(),
    staleTime: Infinity,
  });
  const caseQuery = useQuery({
    queryKey: queryKeys.evalCase(caseKey ?? ""),
    queryFn: () => apiClient.getEvalCase(caseKey ?? ""),
    enabled: caseKey !== undefined,
  });
  const shape = shapesQuery.data?.[evalName];
  const existing = caseQuery.data;

  if (shapesQuery.isError || caseQuery.isError) {
    return (
      <LoadFailed
        title="Couldn’t load the case"
        body="Nothing was changed."
        onRetry={() => {
          void shapesQuery.refetch();
          void caseQuery.refetch();
        }}
      />
    );
  }
  if (
    shape === undefined ||
    (caseKey !== undefined && existing === undefined)
  ) {
    return <LoadingPanel shape="card" label="Loading the case" />;
  }
  return (
    <EvalCaseForm
      key={existing?.key ?? "new"}
      evalName={evalName}
      shape={shape}
      existing={existing}
    />
  );
}
