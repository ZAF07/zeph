import { TaggingResultPart } from "@/components/TaggingResultPart";
import { TaggingResultRow } from "@/components/TaggingResultRow";
import type { TaggingResult } from "@/lib/api-client";
import {
  describeDropped,
  describeExpected,
  describeKept,
} from "@/lib/tagging-results";

const matchPill = "bg-cream text-ink";
const missPill = "border border-danger text-danger";
const droppedPill = "border border-line-strong text-soft";

/**
 * What a Tagging case's tagging step did: each Observation expected and
 * whether one like it was kept, each one code kept with its quote, Pattern
 * Type and sign, who it is about, its Life Thread and context line, and
 * each one code dropped with why.
 *
 * @param props - `result` is what the case kept, dropped and expected.
 * @returns The three parts, or a note when the answer couldn't be read.
 */
export function TaggingObservations({ result }: { result: TaggingResult }) {
  return (
    <>
      {result.answered ? null : (
        <p className="m-0 box-border rounded-input border border-line bg-bg-deep px-3.5 py-3 text-[13px] text-text">
          The tagging model’s answer couldn’t be read, so nothing was kept.
        </p>
      )}
      <TaggingResultPart
        label="Expected"
        empty="Nothing to tag, so nothing may be kept."
      >
        {result.expected.map((expected, index) => (
          <TaggingResultRow
            key={index}
            first={index === 0}
            title={describeExpected(expected)}
            pill={
              expected.matched
                ? { label: "Kept", pill: matchPill }
                : { label: "Not kept", pill: missPill }
            }
          />
        ))}
      </TaggingResultPart>
      <TaggingResultPart label="Kept by code" empty="Nothing was kept.">
        {result.kept.map((kept, index) => (
          <TaggingResultRow
            key={index}
            first={index === 0}
            title={`“${kept.quote}”`}
            pill={
              kept.expected
                ? { label: "Expected", pill: matchPill }
                : { label: "Not expected", pill: missPill }
            }
            facts={[
              { label: "Pattern Type and sign", value: describeKept(kept) },
              { label: "Who it’s about", value: kept.about },
              { label: "Life Thread", value: kept.thread ?? "None" },
            ]}
            note={
              <>
                <span className="text-text">Context.</span> {kept.context}
              </>
            }
          />
        ))}
      </TaggingResultPart>
      <TaggingResultPart label="Dropped by code" empty="Nothing was dropped.">
        {result.dropped.map((dropped, index) => (
          <TaggingResultRow
            key={index}
            first={index === 0}
            title={dropped.quote ? `“${dropped.quote}”` : "No quote"}
            pill={{ label: "Dropped", pill: droppedPill }}
            facts={[
              { label: "As written", value: describeDropped(dropped) },
              { label: "Why", value: dropped.reason },
            ]}
          />
        ))}
      </TaggingResultPart>
    </>
  );
}
