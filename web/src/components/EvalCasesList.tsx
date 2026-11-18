"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { primaryButton } from "@/components/button-styles";
import { EmptyState } from "@/components/EmptyState";
import { EvalCaseRow } from "@/components/EvalCaseRow";
import { LoadFailed } from "@/components/LoadFailed";
import type { EvalName } from "@/lib/api-client";
import { evalDetails, evalOrder } from "@/lib/evals";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * One Eval's cases, archived ones too, with links to the other Evals and
 * a button to add a case. Each case can be edited, duplicated or archived.
 *
 * @param props - `evalName` is the Eval whose cases are shown.
 * @returns The list, or a loading, empty or error state.
 */
export function EvalCasesList({ evalName }: { evalName: EvalName }) {
  const apiClient = useApiClient();
  const casesQuery = useQuery({
    queryKey: queryKeys.evalCases(evalName),
    queryFn: () => apiClient.listEvalCases(evalName),
  });
  const cases = casesQuery.data;

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <nav aria-label="Evals" className="flex flex-wrap gap-1.5">
          {evalOrder.map((name) => (
            <Link
              key={name}
              href={`/admin/evals/cases/${name}`}
              aria-current={name === evalName ? "page" : undefined}
              className={`min-h-9 rounded-full px-3 py-1.5 text-sm no-underline ${
                name === evalName
                  ? "bg-hover font-semibold text-ink"
                  : "text-ink-body"
              }`}
            >
              {evalDetails[name].label}
            </Link>
          ))}
        </nav>
        <Link
          href={`/admin/evals/cases/${evalName}/new`}
          className={primaryButton}
        >
          Add case
        </Link>
      </div>
      <p className="m-0 text-caption text-ink-soft">
        {evalDetails[evalName].checks} Archived cases stay so past runs still
        show them, but new runs leave them out.
      </p>

      {casesQuery.isPending ? (
        <div
          aria-busy="true"
          aria-label="Loading cases"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {cases === undefined && casesQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the cases"
          body="Nothing was changed."
          onRetry={() => void casesQuery.refetch()}
        />
      ) : null}

      {cases !== undefined && cases.length === 0 ? (
        <EmptyState
          title={`No ${evalDetails[evalName].label} cases yet`}
          body="Add a case to check a situation you saw go wrong."
        />
      ) : null}

      {cases !== undefined && cases.length > 0 ? (
        <ul className="m-0 flex list-none flex-col overflow-hidden rounded-xl border border-line bg-white p-0">
          {cases.map((evalCase) => (
            <EvalCaseRow key={evalCase.key} evalCase={evalCase} />
          ))}
        </ul>
      ) : null}
    </>
  );
}
