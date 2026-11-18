import type { ReactNode } from "react";

/**
 * One section of the `States` preview sheet: eyebrow, heading, lead line and
 * its samples.
 *
 * @param props - `eyebrow`, `title` and `lead` head the section; `children`
 *   are its `StatesSheetSample`s.
 * @returns The section.
 */
export function StatesSheetSection({
  eyebrow,
  title,
  lead,
  children,
}: {
  eyebrow: string;
  title: string;
  lead: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-5">
      <div>
        <div className="flex items-center gap-3 text-[11px] font-medium tracking-[2.5px] text-soft uppercase">
          <span aria-hidden="true" className="h-px w-[18px] bg-soft" />
          {eyebrow}
        </div>
        <h2 className="mt-[14px] mb-1 text-[24px] font-normal text-cream">
          {title}
        </h2>
        <p className="m-0 max-w-[640px] text-[14px] text-soft">{lead}</p>
      </div>
      <div className="flex flex-wrap items-start gap-6">{children}</div>
    </section>
  );
}
