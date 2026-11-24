import type { ReactNode } from "react";

import { MemoryDetailLine } from "@/components/MemoryDetailLine";

/**
 * One labelled row of a Pattern Type's card, such as "Definition" with its
 * text. Rows after the first are divided by a line.
 *
 * @param props - `label` names the detail and `children` is its value.
 * @returns The row.
 */
export function PatternTypeLine({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <li className="border-t border-line py-3 first:border-t-0">
      <MemoryDetailLine label={label}>{children}</MemoryDetailLine>
    </li>
  );
}
