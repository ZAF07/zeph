import type { ReactNode } from "react";

/**
 * The heading over one part of a form page, such as "Memory" or "Crisis
 * Reply", in the field row's name and caption type.
 *
 * @param props - `id` lets the part be named by it; `title` is the
 *   heading; `caption` is an optional line under it.
 * @returns The heading.
 */
export function FormSectionHeading({
  id,
  title,
  caption,
}: {
  id?: string;
  title: string;
  caption?: ReactNode;
}) {
  return (
    <div>
      <h2 id={id} className="m-0 text-[15px] font-normal text-text">
        {title}
      </h2>
      {caption ? <p className="m-0 text-[13px] text-soft">{caption}</p> : null}
    </div>
  );
}
