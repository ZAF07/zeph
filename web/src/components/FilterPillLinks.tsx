import Link from "next/link";

import { filterPillClass } from "@/components/filter-pill-styles";

/** One link in a row of filter pill links. */
export type FilterPillLink = { href: string; label: string };

/**
 * A row of filter pills that are links to other pages, such as the Evals
 * whose cases can be listed. The current page's pill is cream.
 *
 * @param props - `label` names the row, `links` are the pills and
 *   `currentHref` is the page being viewed.
 * @returns The links.
 */
export function FilterPillLinks({
  label,
  links,
  currentHref,
}: {
  label: string;
  links: FilterPillLink[];
  currentHref: string;
}) {
  return (
    <nav aria-label={label} className="flex flex-wrap gap-1.5">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={link.href === currentHref ? "page" : undefined}
          className={filterPillClass(link.href === currentHref)}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
