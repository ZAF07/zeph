import type { ReactNode } from "react";

/**
 * One part of a Tagging result: its label, then its rows, or a line saying
 * it has none.
 *
 * @param props - `label` heads it, `empty` is the line shown with no rows
 *   and `children` are the rows.
 * @returns The part.
 */
export function TaggingResultPart({
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
