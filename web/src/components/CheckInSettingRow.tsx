import type { ReactNode } from "react";

/**
 * One row of the Check-ins settings card: the setting's name and a short
 * line on the left, and its control on the right, wrapping under on a
 * narrow screen. Rows are divided by a line.
 *
 * @param props - `title` names the setting, `caption` explains it and
 *   `children` is the control, with any "changed in chat" note under it.
 * @returns The row.
 */
export function CheckInSettingRow({
  title,
  caption,
  children,
}: {
  title: string;
  caption: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-t border-line py-[18px]">
      <div className="flex-[1_1_220px]">
        <div className="text-[15px] font-normal text-text">{title}</div>
        <div className="text-[13px] text-soft">{caption}</div>
      </div>
      <div className="flex min-w-0 flex-[1_1_320px] flex-col items-start gap-1.5">
        {children}
      </div>
    </div>
  );
}
