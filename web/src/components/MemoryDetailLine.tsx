import type { ReactNode } from "react";

/**
 * One labelled line inside a memory card, such as "Feeling · Anxious,
 * restless". The value moves under the label when the card is narrow.
 *
 * @param props - `label` names the detail and `children` is its value.
 * @returns The line.
 */
export function MemoryDetailLine({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[14px]">
      <span className="flex-[0_0_96px] text-soft">{label}</span>
      <span className="flex-[1_1_240px] text-text">{children}</span>
    </div>
  );
}
