import type { ReactNode } from "react";

import { FieldRows } from "@/components/FieldRows";
import { FormSectionHeading } from "@/components/FormSectionHeading";

/**
 * One named part of a Pattern Type's card, such as "Signs": a heading over
 * a box of rows.
 *
 * @param props - `id` names the group for screen readers; `title` is its
 *   heading; `caption` is the line under it; `children` are its
 *   `PatternTypeLine` and `PatternTypeEntry` rows.
 * @returns The group.
 */
export function PatternTypeGroup({
  id,
  title,
  caption,
  children,
}: {
  id: string;
  title: string;
  caption?: string;
  children: ReactNode;
}) {
  return (
    <div role="group" aria-labelledby={id} className="flex flex-col gap-3">
      <FormSectionHeading id={id} title={title} caption={caption} />
      <FieldRows>{children}</FieldRows>
    </div>
  );
}
