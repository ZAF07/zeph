"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { tabClass, tabRow } from "@/components/tab-styles";

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
  {
    label: "Model Prices",
    href: "/admin/evals/costs",
    isActive: (pathname: string) => pathname.startsWith("/admin/evals/costs"),
  },
];

/**
 * The Eval area's parts: its runs, its cases, the Judge and the Model
 * Prices, drawn as the Memories tab row, with the part being viewed
 * chosen.
 *
 * @returns The links.
 */
export function EvalAreaTabs() {
  const pathname = usePathname();
  return (
    <nav aria-label="Eval area" className={tabRow}>
      {tabs.map((tab) => {
        const isActive = tab.isActive(pathname);
        return (
          <Link
            key={tab.label}
            href={tab.href}
            aria-current={isActive ? "page" : undefined}
            className={tabClass(isActive)}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
