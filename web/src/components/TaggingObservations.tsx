import type { ReactNode } from "react";

import { EvalPill } from "@/components/EvalPill";
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
 * One row of a Tagging result: a title with its pill, then any facts side
 * by side and a line under them, drawn like a Day Summary answer.
 *
 * @param props - `first` is true for the list's first row, which has no
 *   line above it; `title` and `pill` head the row; `facts` are label and
 *   value pairs; `note` is the line under them.
 * @returns The row.
 */
function ResultRow({
  first,
  title,
  pill,
  facts = [],
  note,
}: {
  first: boolean;
  title: string;
  pill: { label: string; pill: string };
  facts?: { label: string; value: string }[];
  note?: ReactNode;
}) {
  return (
    <div
      className={`flex flex-col gap-2 py-3.5 ${first ? "" : "border-t border-line"}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <span className="min-w-0 flex-[1_1_320px] text-[15px] font-normal text-text">
          {title}
        </span>
        <EvalPill {...pill} />
      </div>
      {facts.length > 0 ? (
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-[14px]">
          {facts.map((fact) => (
            <div key={fact.label} className="min-w-0 flex-[1_1_200px]">
              <div className="text-[12px] text-soft">{fact.label}</div>
              <div className="text-text">{fact.value}</div>
            </div>
          ))}
        </div>
      ) : null}
      {note ? <div className="text-[13px] text-soft">{note}</div> : null}
    </div>
  );
}

/**
 * One part of a Tagging result: its label, then its rows, or a line saying
 * it has none.
 *
 * @param props - `label` heads it, `empty` is the line shown with no rows
 *   and `children` are the rows.
 * @returns The part.
 */
function ResultPart({
  label,
  empty,
  children,
}: {
  label: string;
  empty: string;
  children: ReactNode[];
}) {
  return (
    <div>
      <div className="pb-1.5 text-[12px] text-soft">{label}</div>
      {children.length > 0 ? (
        children
      ) : (
        <p className="m-0 py-3.5 text-[14px] text-soft">{empty}</p>
      )}
    </div>
  );
}

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
      <ResultPart
        label="Expected"
        empty="Nothing to tag, so nothing may be kept."
      >
        {result.expected.map((expected, index) => (
          <ResultRow
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
      </ResultPart>
      <ResultPart label="Kept by code" empty="Nothing was kept.">
        {result.kept.map((kept, index) => (
          <ResultRow
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
      </ResultPart>
      <ResultPart label="Dropped by code" empty="Nothing was dropped.">
        {result.dropped.map((dropped, index) => (
          <ResultRow
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
      </ResultPart>
    </>
  );
}
