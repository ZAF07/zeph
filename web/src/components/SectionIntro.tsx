import type { ReactNode } from "react";

import { Eyebrow } from "@/components/Eyebrow";

/**
 * The eyebrow, heading and line that open a section of Landing or How It
 * Works.
 *
 * @param props - `eyebrow` is the small label, `title` the heading, `body`
 *   the line under it, and `className` sizes the block inside its section.
 * @returns The section intro.
 */
export function SectionIntro({
  eyebrow,
  title,
  body,
  className,
}: {
  eyebrow: string;
  title: ReactNode;
  body: string;
  className: string;
}) {
  return (
    <div className={className}>
      <Eyebrow>{eyebrow}</Eyebrow>
      <h2 className="mt-[18px] mb-[14px] text-[34px] leading-[1.15] font-normal tracking-[-0.3px] text-cream">
        {title}
      </h2>
      <p className="m-0 text-soft">{body}</p>
    </div>
  );
}
