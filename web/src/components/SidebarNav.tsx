"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useIsAdmin } from "@/lib/use-is-admin";

/** One link in the Dashboard sidebar. */
export type SidebarItem = {
  id: string;
  label: string;
  href: string;
  iconPath: string;
};

/** The admin pages built so far; later issues add the rest. */
const adminItems = [
  { label: "Users", href: "/admin/users" },
  { label: "Persona", href: "/admin/persona" },
  { label: "Prompts & models", href: "/admin/prompts" },
  { label: "Safety", href: "/admin/safety" },
  { label: "Safeguard Events", href: "/admin/safeguard-events" },
  { label: "Knowledge", href: "/admin/knowledge" },
  { label: "Memory Categories", href: "/admin/memory-categories" },
  { label: "Platform settings", href: "/admin/settings" },
];

/**
 * The sidebar's page links, highlighting the page being viewed. Admins also
 * see an Admin group of links.
 *
 * @param props - `items` are the User page links to show.
 * @returns The navigation.
 */
export function SidebarNav({ items }: { items: SidebarItem[] }) {
  const pathname = usePathname();
  const isAdmin = useIsAdmin();
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

      {isAdmin ? (
        <div
          role="group"
          aria-labelledby="sidebar-admin-heading"
          className="flex flex-col gap-1.5 border-t border-line pt-4"
        >
          <span
            id="sidebar-admin-heading"
            className="px-3 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted"
          >
            Admin
          </span>
          <ul className="m-0 flex list-none flex-wrap gap-px p-0">
            {adminItems.map((item) => {
              const isActive = item.href === pathname;
              return (
                <li key={item.href} className="flex-[1_1_150px]">
                  <Link
                    href={item.href}
                    aria-current={isActive ? "page" : undefined}
                    className={`flex min-h-10 items-center rounded-lg px-3 py-2 text-sm no-underline ${
                      isActive
                        ? "bg-hover font-semibold text-ink"
                        : "bg-transparent text-ink-body"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </nav>
  );
}
