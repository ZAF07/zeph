"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalPill } from "@/components/EvalPill";
import { LoadFailed } from "@/components/LoadFailed";
import { ApiError, type CaseHistoryEntry } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import { countOf, evalDetails, outcomeLabels } from "@/lib/evals";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * Says what changed between a result and the older one after it.
 *
 * @param entry - The newer result.
 * @returns E.g. "Case changed · 2 settings changed: persona, judge.model";
 *   "" when nothing changed.
 */
function describeChanges(entry: CaseHistoryEntry): string {
  const parts = [];
  if (entry.case_changed) {
    parts.push("Case changed");
  }
  if (entry.changed_settings.length > 0) {
    parts.push(
      `${countOf(entry.changed_settings.length, "setting")} changed: ${entry.changed_settings.join(", ")}`,
    );
  }
  return parts.join(" · ");
}

/**
 * One Eval Case's pass or fail in its recent runs, newest first. A line
 * between two results marks where the case or the settings changed, so an
 * Admin can tell what caused a change in results.
 *
 * @param props - `caseKey` is the case's key.
 * @returns The page body, or a loading, not-found or error state.
 */
export function CaseHistoryView({ caseKey }: { caseKey: string }) {
  const apiClient = useApiClient();
  const historyQuery = useQuery({
    queryKey: queryKeys.caseHistory(caseKey),
    queryFn: () => apiClient.getCaseHistory(caseKey),
  });
  const history = historyQuery.data;
  const isNotFound =
    historyQuery.error instanceof ApiError && historyQuery.error.status === 404;

  const backLink = (
    <Link href="/admin/evals" className="w-fit text-sm font-medium">
      ← Eval Runs
    </Link>
  );

  if (history === undefined) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        {historyQuery.isPending ? (
          <div
            aria-busy="true"
            aria-label="Loading the case"
            className="h-[320px] rounded-xl border border-line bg-subtle"
          />
        ) : isNotFound ? (
          <p className="m-0 rounded-card border border-dashed border-line-strong px-6 py-16 text-center text-caption text-ink-muted">
            There’s no case named {caseKey}.
          </p>
        ) : (
          <LoadFailed
            title="Couldn’t load this case"
            body="Its results are still kept."
            onRetry={() => void historyQuery.refetch()}
          />
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-[22px]">
      {backLink}
      <AdminPageHeader
        title={history.case.key}
        lead={`${evalDetails[history.case.eval].label} case${
          history.case.archived ? ", archived" : ""
        }. How it went in its most recent runs, newest first.`}
      />
      <details className="rounded-xl border border-line bg-white px-[18px] py-3.5">
        <summary className="cursor-pointer font-medium">The case now</summary>
        <pre className="m-0 mt-2 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-subtle px-3 py-2 font-mono text-xs">
          {JSON.stringify(history.case.content, null, 2)}
        </pre>
      </details>
      {history.entries.length === 0 ? (
        <p className="m-0 rounded-card border border-dashed border-line-strong px-6 py-12 text-center text-caption text-ink-muted">
          This case hasn’t run yet.
        </p>
      ) : (
        <ol className="m-0 flex list-none flex-col gap-0 p-0">
          {history.entries.map((entry) => {
            const changes = describeChanges(entry);
            return (
              <li key={entry.result_id} className="flex flex-col">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-line bg-white px-[18px] py-3">
                  <EvalPill {...outcomeLabels[entry.outcome]} />
                  <Link href={`/admin/evals/runs/${entry.run_id}`}>
                    {formatSavedAt(entry.run_queued_at)}
                  </Link>
                  <Link
                    href={`/admin/evals/runs/${entry.run_id}/results/${entry.result_id}`}
                    className="ml-auto text-caption"
                  >
                    Full trace
                  </Link>
                </div>
                {changes ? (
                  <p
                    aria-label="Changed since the run before"
                    className="m-0 ml-[18px] border-l-2 border-yellow-deep py-2 pl-3 text-caption text-yellow-deep"
                  >
                    Changed since the run below: {changes}
                  </p>
                ) : (
                  <div className="h-2.5" />
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
