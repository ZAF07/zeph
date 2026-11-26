import Link from "next/link";

import { DaySummaryAnswers } from "@/components/DaySummaryAnswers";
import { EvalPill } from "@/components/EvalPill";
import { TaggingObservations } from "@/components/TaggingObservations";
import { WholePipelinePatterns } from "@/components/WholePipelinePatterns";
import type { CaseResult } from "@/lib/api-client";
import { countOf, evalDetails, groupChecks, outcomeLabels } from "@/lib/evals";
import { formatDuration, formatTokens } from "@/lib/model-calls";

/**
 * One Case Result: its outcome, tokens and time, then each check with its
 * reason, any error and, for a failed case, the notes that help read it. A
 * Day Summary case shows the Summary written and each question's answer
 * instead of its checks; a Tagging case shows what was expected, kept and
 * dropped; a Whole-pipeline case shows each Pattern that became ready or
 * was shared and the true ones missed. It links to the result's full trace
 * and to the case's history.
 *
 * @param props - `runId` is the run it belongs to; `result` is the Case
 *   Result; `tryLabel`, when given, says which try it is, e.g. "Try 2 of 3".
 * @returns The result's card.
 */
export function CaseResultCard({
  runId,
  result,
  tryLabel,
}: {
  runId: string;
  result: CaseResult;
  tryLabel?: string;
}) {
  const failedChecks = result.checks.filter((check) => !check.passed).length;
  return (
    <li
      aria-label={result.case_key}
      className="flex flex-col gap-2.5 rounded-card border border-line bg-panel px-[18px] py-3.5 text-[14px] text-text"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <EvalPill {...outcomeLabels[result.outcome]} />
        <Link
          href={`/admin/evals/history/${encodeURIComponent(result.case_key)}`}
          className="underline"
          title="This case in recent runs"
        >
          {result.case_key}
        </Link>
        <span className="text-soft">{evalDetails[result.eval].label}</span>
        {tryLabel ? <span className="text-soft">· {tryLabel}</span> : null}
        <span className="ml-auto whitespace-nowrap text-[13px] text-soft">
          {formatTokens(result.tokens_in, result.tokens_out)} ·{" "}
          {formatDuration(result.duration_ms)} ·{" "}
          <Link
            href={`/admin/evals/runs/${runId}/results/${result.id}`}
            className="underline"
          >
            Full trace
          </Link>
        </span>
      </div>
      {result.error ? (
        <p className="m-0 rounded-note border border-danger px-3.5 py-2 text-[13px] text-danger">
          Couldn’t be checked: {result.error}
        </p>
      ) : null}
      {result.day_summary ? (
        <DaySummaryAnswers result={result.day_summary} />
      ) : result.tagging ? (
        <TaggingObservations result={result.tagging} />
      ) : result.whole_pipeline ? (
        <WholePipelinePatterns result={result.whole_pipeline} />
      ) : result.checks.length > 0 ? (
        <details open={result.outcome !== "pass"}>
          <summary className="cursor-pointer text-[13px] text-soft">
            {countOf(result.checks.length, "check")}
            {failedChecks > 0 ? `, ${failedChecks} failed` : ""}
          </summary>
          <div className="mt-2 flex flex-col gap-2">
            {groupChecks(result.checks).map(({ group, checks }) => (
              <div key={group} className="flex flex-col gap-1">
                {group ? (
                  <p className="m-0 text-[13px] text-text">“{group}”</p>
                ) : null}
                <ul className="m-0 flex list-none flex-col gap-1 p-0">
                  {checks.map((check, index) => (
                    <li
                      key={`${check.name}-${index}`}
                      className="text-[13px] text-text"
                    >
                      <span
                        className={
                          check.passed
                            ? "font-mono text-[12px] text-cream"
                            : "font-mono text-[12px] text-danger"
                        }
                      >
                        {check.passed ? "PASS" : "FAIL"}
                      </span>{" "}
                      <span className="text-cream">{check.name}</span>:{" "}
                      {check.detail}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
      ) : null}
      {result.outcome === "fail" &&
      result.notes.length > 0 &&
      !result.day_summary &&
      !result.tagging ? (
        <details>
          <summary className="cursor-pointer text-[13px] text-soft">
            What happened
          </summary>
          <pre className="m-0 mt-2 rounded-input bg-bg-deep px-3 py-2 font-mono text-[12px] leading-relaxed whitespace-pre-wrap">
            {result.notes.join("\n")}
          </pre>
        </details>
      ) : null}
    </li>
  );
}
