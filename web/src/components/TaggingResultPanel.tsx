import { EvalPill } from "@/components/EvalPill";
import { TaggingObservations } from "@/components/TaggingObservations";
import type { TaggingResult } from "@/lib/api-client";
import { taggingVerdict } from "@/lib/tagging-results";

/**
 * One Tagging case's result as a panel: its key, whether it passed and how
 * it differs, then what was expected, kept and dropped.
 *
 * @param props - `caseKey` names the case; `result` is what it kept,
 *   dropped and expected.
 * @returns The panel.
 */
export function TaggingResultPanel({
  caseKey,
  result,
}: {
  caseKey: string;
  result: TaggingResult;
}) {
  const verdict = taggingVerdict(result);
  return (
    <section
      aria-label="Result"
      className="box-border flex flex-col gap-[14px] rounded-card border border-line bg-panel px-6 py-[22px]"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="m-0 font-mono text-[17px] font-normal text-cream">
          {caseKey}
        </h2>
        <EvalPill
          label={verdict}
          pill={
            verdict === "Passed"
              ? "bg-cream text-ink"
              : "border border-danger text-danger"
          }
        />
      </div>
      <TaggingObservations result={result} />
    </section>
  );
}
