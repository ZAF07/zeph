import type { ReactNode } from "react";

import { cardListRow } from "@/components/card-styles";

/**
 * One listed row of a Pattern Type's card, such as a sign or a look-alike:
 * its text, a softer line under it, and its tags at the right.
 *
 * @param props - `title` is the row's text; `detail` is the softer line
 *   under it; `tags` are its pills, such as a sign's strength.
 * @returns The row.
 */
export function PatternTypeEntry({
  title,
  detail,
  tags,
}: {
  title: string;
  detail?: string;
  tags?: ReactNode;
}) {
  return (
    <li className={cardListRow}>
      <div className="min-w-0 flex-[1_1_260px]">
        <div className="text-[14px] text-text">{title}</div>
        {detail ? <div className="text-[13px] text-soft">{detail}</div> : null}
      </div>
      {tags ? <div className="flex flex-wrap gap-2">{tags}</div> : null}
    </li>
  );
}
