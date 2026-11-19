import type { ReactNode } from "react";

/**
 * The heading of an admin page: an "Admin" eyebrow, the title and a lead,
 * as the admin page references draw it.
 *
 * @param props - `title` names the page (with a "To build" tag when it has
 *   one); `lead` says what it is for; `aside` sits at the right, such as the
 *   Overview's "Sample data" label.
 * @returns The header.
 */
export function AdminPageHeader({
  title,
  lead,
  aside,
}: {
  title: ReactNode;
  lead: string;
  aside?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0 flex-[1_1_380px]">
        <div className="flex items-center gap-3 text-[11px] font-medium tracking-[2.5px] text-soft uppercase">
          <span aria-hidden="true" className="h-px w-[18px] bg-soft" />
          Admin
        </div>
        <h1 className="mt-[14px] mb-0 flex items-center text-[32px] leading-[1.15] font-normal text-cream">
          {title}
        </h1>
        <p className="mt-1.5 mb-0 max-w-[640px] text-[14px] text-soft">
          {lead}
        </p>
      </div>
      {aside}
    </header>
  );
}
