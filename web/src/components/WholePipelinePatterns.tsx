import { TaggingResultPart } from "@/components/TaggingResultPart";
import { TaggingResultRow } from "@/components/TaggingResultRow";
import type { WholePipelineResult } from "@/lib/api-client";
import { countOf } from "@/lib/evals";
import {
  describeBlockedBy,
  describePattern,
  describeState,
} from "@/lib/whole-pipeline-results";

const truePill = "bg-cream text-ink";
const notTruePill = "border border-danger text-danger";
const missedPill = "border border-line-strong text-soft";

/**
 * What a Whole-pipeline case found: each Pattern that became ready or was
 * shared and whether it is one of the made-up User's true ones, then each
 * true one that never became ready and where it stopped. Drawn with the
 * parts of a Tagging result.
 *
 * @param props - `result` is the ready or shared Patterns and the true
 *   ones missed.
 * @returns The two parts.
 */
export function WholePipelinePatterns({
  result,
}: {
  result: WholePipelineResult;
}) {
  const found = result.true_count - result.missed.length;
  return (
    <>
      <p className="m-0 text-[13px] text-soft">
        {countOf(result.conversations, "Conversation")} · {found} of{" "}
        {result.true_count} true{" "}
        {result.true_count === 1 ? "Pattern" : "Patterns"} found
      </p>
      <TaggingResultPart
        label="Became ready or shared"
        empty="No Pattern became ready."
      >
        {result.patterns.map((pattern, index) => (
          <TaggingResultRow
            key={pattern.pattern_type}
            first={index === 0}
            title={describePattern(pattern)}
            pill={
              pattern.is_true
                ? { label: "True", pill: truePill }
                : { label: "Not true", pill: notTruePill }
            }
            facts={[
              {
                label: "Got as far as",
                value: pattern.shared ? "Shared" : "Ready",
              },
              { label: "Stands now", value: describeState(pattern.state) },
            ]}
          />
        ))}
      </TaggingResultPart>
      <TaggingResultPart
        label="True Patterns missed"
        empty={
          result.true_count === 0
            ? "None is true of this made-up User."
            : "None missed."
        }
      >
        {result.missed.map((missed, index) => (
          <TaggingResultRow
            key={missed.pattern_type}
            first={index === 0}
            title={describePattern(missed)}
            pill={{ label: "Missed", pill: missedPill }}
            facts={[
              { label: "Stands now", value: describeState(missed.state) },
              {
                label: "Stopped by",
                value: describeBlockedBy(missed.blocked_by),
              },
            ]}
          />
        ))}
      </TaggingResultPart>
    </>
  );
}
