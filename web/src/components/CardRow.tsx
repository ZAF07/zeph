import type { ReactNode } from "react";

/**
 * One 48px row of a card's list, such as a payment in Billing history or a
 * line of Needs attention. Its parts spread across the row and wrap when
 * there is no room. Rows after the first are divided by a line.
 *
 * @param props - `children` are the row's parts, left to right.
 * @returns The row.
 */
export function CardRow({ children }: { children: ReactNode }) {
  return (
    <div className="box-content flex min-h-12 flex-wrap items-center justify-between gap-x-4 gap-y-1 border-t border-line first:border-t-0">
      {children}
    </div>
  );
}
