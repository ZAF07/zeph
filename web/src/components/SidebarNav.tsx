"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** One link in the Dashboard sidebar. */
export type SidebarItem = {
  id: string;
  label: string;
  href: string;
  iconPath: string;
};

/**
 * The sidebar's page links, highlighting the page being viewed.
 *
 * @param props - `items` are the links to show.
 * @returns The navigation list.
 */
export function SidebarNav({ items }: { items: SidebarItem[] }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Dashboard" className="flex flex-col gap-5">
      <ul className="m-0 flex list-none flex-wrap gap-0.5 p-0">
        {items.map((item) => {
          const isActive = item.href === pathname;
          return (
            <li key={item.id} className="flex-[1_1_150px]">
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`flex min-h-11 items-center gap-3 rounded-input px-3 py-2.5 text-[15px] no-underline ${
                  isActive
                    ? "bg-hover font-semibold text-ink"
                    : "bg-transparent text-ink-body"
                }`}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                  className="flex-none"
                >
                  <path d={item.iconPath} />
                </svg>
                <span className="flex-1">{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
