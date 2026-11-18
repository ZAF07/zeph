import type { ReactNode } from "react";

/**
 * The plain heading at the top of a Dashboard page with no illustration: a
 * small label, the page title and one line under it.
 *
 * @param props - `eyebrow` is the small label, `title` the page title and
 *   `lead` the line under it.
 * @returns The header.
 */
export function PageHeader({
  eyebrow,
  title,
  lead,
}: {
  eyebrow: string;
  title: string;
  lead: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-4">
      <div className="min-w-0 flex-[1_1_380px]">
        <div className="flex items-center gap-3 text-[11px] font-medium tracking-[2.5px] text-soft uppercase">
          <span aria-hidden="true" className="h-px w-[18px] bg-soft" />
          {eyebrow}
        </div>
        <h1 className="mt-[14px] mb-2 text-[32px] leading-[1.15] font-normal text-cream">
          {title}
        </h1>
        <p className="m-0 max-w-[600px] text-[15px] text-soft">{lead}</p>
      </div>
    </header>
  );
}
