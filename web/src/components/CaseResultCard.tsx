import Link from "next/link";

import { EvalPill } from "@/components/EvalPill";
import type { CaseResult } from "@/lib/api-client";
import { countOf, evalDetails, groupChecks, outcomeLabels } from "@/lib/evals";
import { formatDuration, formatTokens } from "@/lib/model-calls";

/**
 * One Case Result: its outcome, tokens and time, then each check with its
 * reason, any error and, for a failed case, the notes that help read it. It
 * links to the result's full trace and to the case's history.
 *
 * @param props - `runId` is the run it belongs to; `result` is the Case
 *   Result.
 * @returns The result's card.
 */
export function CaseResultCard({
  runId,
  result,
}: {
  runId: string;
  result: CaseResult;
}) {
  const failedChecks = result.checks.filter((check) => !check.passed).length;
  return (
    <li
      aria-label={result.case_key}
      className="flex flex-col gap-2.5 rounded-xl border border-line bg-white px-[18px] py-3.5"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <EvalPill {...outcomeLabels[result.outcome]} />
        <Link
          href={`/admin/evals/history/${encodeURIComponent(result.case_key)}`}
          className="font-medium"
          title="This case in recent runs"
        >
          {result.case_key}
        </Link>
        <span className="text-ink-muted">{evalDetails[result.eval].label}</span>
        <span className="ml-auto whitespace-nowrap text-caption text-ink-muted">
          {formatTokens(result.tokens_in, result.tokens_out)} ·{" "}
          {formatDuration(result.duration_ms)} ·{" "}
          <Link href={`/admin/evals/runs/${runId}/results/${result.id}`}>
            Full trace
          </Link>
        </span>
      </div>
      {result.error ? (
        <p className="m-0 rounded-lg bg-yellow-tint px-3 py-2 text-caption text-yellow-deep">
          Couldn’t be checked: {result.error}
        </p>
      ) : null}
      {result.checks.length > 0 ? (
        <details open={result.outcome !== "pass"}>
          <summary className="cursor-pointer text-caption text-ink-soft">
            {countOf(result.checks.length, "check")}
            {failedChecks > 0 ? `, ${failedChecks} failed` : ""}
          </summary>
          <div className="mt-2 flex flex-col gap-2">
            {groupChecks(result.checks).map(({ group, checks }) => (
              <div key={group} className="flex flex-col gap-1">
                {group ? (
                  <p className="m-0 text-caption font-medium">“{group}”</p>
                ) : null}
                <ul className="m-0 flex list-none flex-col gap-1 p-0">
                  {checks.map((check, index) => (
                    <li
                      key={`${check.name}-${index}`}
                      className="text-caption text-ink-body"
                    >
                      <span
                        className={
                          check.passed
                            ? "font-mono text-xs text-blue-deep"
                            : "font-mono text-xs text-danger-deep"
                        }
                      >
                        {check.passed ? "PASS" : "FAIL"}
                      </span>{" "}
                      <span className="font-medium">{check.name}</span>:{" "}
                      {check.detail}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
      ) : null}
      {result.outcome === "fail" && result.notes.length > 0 ? (
        <details>
          <summary className="cursor-pointer text-caption text-ink-soft">
            What happened
          </summary>
          <pre className="m-0 mt-2 whitespace-pre-wrap rounded-lg bg-subtle px-3 py-2 font-mono text-xs leading-relaxed">
            {result.notes.join("\n")}
          </pre>
        </details>
      ) : null}
    </li>
  );
}
