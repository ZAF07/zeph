import type { ReactNode } from "react";

/**
 * One line of a card's details, with a label at the left and its value at
 * the right, such as "Quiet hours · 11:00 PM to 7:00 AM". Rows after the
 * first are divided by a line.
 *
 * @param props - `label` names the detail and `children` is its value.
 * @returns The row.
 */
export function DetailRow({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="box-content flex min-h-11 flex-wrap items-center justify-between gap-x-4 gap-y-1 border-t border-line first:border-t-0">
      <span className="text-[14px] text-soft">{label}</span>
      <span className="flex flex-col items-end text-[14px] text-text">
        {children}
      </span>
    </div>
  );
}
