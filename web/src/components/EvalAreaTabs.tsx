"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  {
    label: "Runs",
    href: "/admin/evals",
    isActive: (pathname: string) =>
      pathname === "/admin/evals" ||
      pathname.startsWith("/admin/evals/runs") ||
      pathname.startsWith("/admin/evals/new"),
  },
  {
    label: "Cases",
    href: "/admin/evals/cases/safeguard",
    isActive: (pathname: string) => pathname.startsWith("/admin/evals/cases"),
  },
  {
    label: "Judge",
    href: "/admin/evals/judge",
    isActive: (pathname: string) => pathname.startsWith("/admin/evals/judge"),
  },
];

/**
 * The Eval area's parts: its runs, its cases and the Judge, highlighting
 * the part being viewed.
 *
 * @returns The links.
 */
export function EvalAreaTabs() {
  const pathname = usePathname();
  return (
    <nav aria-label="Eval area" className="flex flex-wrap gap-1.5">
      {tabs.map((tab) => {
        const isActive = tab.isActive(pathname);
        return (
          <Link
            key={tab.label}
            href={tab.href}
            aria-current={isActive ? "page" : undefined}
            className={`min-h-10 rounded-full border px-3.5 py-2 text-sm font-medium no-underline ${
              isActive
                ? "border-ink bg-ink text-white hover:text-white"
                : "border-line-strong bg-transparent text-ink-body"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
