import { DaySummaryAnswers } from "@/components/DaySummaryAnswers";
import { EvalPill } from "@/components/EvalPill";
import type { DaySummaryResult } from "@/lib/api-client";

/**
 * One Day Summary case's result as a panel: its key, how many questions
 * missed, then the Summary and each answer.
 *
 * @param props - `caseKey` names the case; `result` is its Day Summary and
 *   answers.
 * @returns The panel.
 */
export function DaySummaryResultPanel({
  caseKey,
  result,
}: {
  caseKey: string;
  result: DaySummaryResult;
}) {
  const missed = result.answers.filter((answer) => !answer.matched).length;
  return (
    <section
      aria-label="Result"
      className="box-border flex flex-col gap-[14px] rounded-card border border-line bg-panel px-6 py-[22px]"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="m-0 font-mono text-[17px] font-normal text-cream">
          {caseKey}
        </h2>
        {missed > 0 ? (
          <EvalPill
            label={`Failed · ${missed} of ${result.answers.length} missed`}
            pill="border border-danger text-danger"
          />
        ) : (
          <EvalPill label="Passed" pill="bg-cream text-ink" />
        )}
      </div>
      <DaySummaryAnswers result={result} />
    </section>
  );
}
