import Link from "next/link";
import type { ReactNode } from "react";

/**
 * The header on the signed-out pages: the Zeph wordmark and nav links on the
 * left, actions on the right. Below 900px it takes the phone layout and the
 * nav links are hidden.
 *
 * @param props - `wordmark` is the Zeph wordmark linking home and
 *   `homeLinkLabel` that link's name for screen readers; `nav` is the nav
 *   links, if any; `actions` sits on the right.
 * @returns The header.
 */
export function PublicHeader({
  wordmark,
  homeLinkLabel,
  nav,
  actions,
}: {
  wordmark: string;
  homeLinkLabel: string;
  nav?: ReactNode;
  actions: ReactNode;
}) {
  return (
    <header className="mx-auto box-border flex max-w-[1160px] flex-wrap items-center justify-between gap-x-8 gap-y-3 px-8 py-[14px] text-[14px] font-normal max-[899px]:mx-0 max-[899px]:max-w-none max-[899px]:flex-nowrap max-[899px]:gap-2 max-[899px]:py-2.5 max-[899px]:pr-3 max-[899px]:pl-5">
      <div className="flex flex-wrap items-center gap-x-12 gap-y-2">
        <Link
          href="/"
          aria-label={homeLinkLabel}
          className="text-[26px] font-normal tracking-[0.2px] text-cream no-underline max-[899px]:text-[24px]"
        >
          {wordmark}
        </Link>
        <nav className="flex flex-wrap items-center gap-x-2.5 gap-y-1 max-[899px]:hidden">
          {nav}
        </nav>
      </div>
      <div className="flex items-center gap-3 max-[899px]:gap-1.5">
        {actions}
      </div>
    </header>
  );
}
