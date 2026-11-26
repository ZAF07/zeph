import type { ReactNode } from "react";

import { EvalPill } from "@/components/EvalPill";

/**
 * One row of a Tagging result: a title with its pill, then any facts side
 * by side and a line under them, drawn like a Day Summary answer.
 *
 * @param props - `first` is true for the list's first row, which has no
 *   line above it; `title` and `pill` head the row; `facts` are label and
 *   value pairs; `note` is the line under them.
 * @returns The row.
 */
export function TaggingResultRow({
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
