"use client";

import Link from "next/link";
import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { PublicHeader } from "@/components/PublicHeader";
import type { SiteHeaderWords } from "@/components/site-links";

/** The phone nav panel's id, which the menu button points to. */
const SITE_MENU_ID = "site-menu";

/**
 * The header on Landing and How It Works. At 900px and wider it shows the
 * nav links, "Log in" and "Get Started". Below that, only "Get Started" and
 * the menu button stay; the button opens the nav panel under the header,
 * pushing the page down, and choosing a link closes it.
 *
 * @param props - `words` is the header's words, from Copy.
 * @returns The header, and the nav panel while it is open.
 */
export function SiteHeader({ words }: { words: SiteHeaderWords }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <PublicHeader
        wordmark={words.wordmark}
        homeLinkLabel={words.homeLinkLabel}
        nav={words.navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="px-3.5 py-2.5 text-text no-underline"
          >
            {link.label}
          </Link>
        ))}
        actions={
          <>
            <Link
              href="/sign-in"
              className="px-3.5 py-2.5 text-text no-underline max-[899px]:hidden"
            >
              {words.logIn}
            </Link>
            <Link href="/sign-up" className={primaryButton}>
              {words.signUp}{" "}
              <span aria-hidden="true" className="ml-2.5 max-[899px]:hidden">
                →
              </span>
            </Link>
            <button
              type="button"
              aria-label={menuOpen ? words.closeMenu : words.openMenu}
              aria-expanded={menuOpen}
              aria-controls={SITE_MENU_ID}
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex size-11 flex-none cursor-pointer items-center justify-center rounded-input border-0 bg-transparent text-text min-[900px]:hidden"
            >
              <svg
                aria-hidden="true"
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              >
                <path
                  d={
                    menuOpen
                      ? "M6 6l12 12M18 6L6 18"
                      : "M4 7h16M4 12h16M4 17h16"
                  }
                />
              </svg>
            </button>
          </>
        }
      />
      {menuOpen ? (
        <nav
          id={SITE_MENU_ID}
          aria-label={words.menuLabel}
          className="flex flex-col border-b border-line bg-bg-deep/94 px-5 pb-3 min-[900px]:hidden"
        >
          {[...words.navLinks, { href: "/sign-in", label: words.logIn }].map(
            (link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="box-content flex min-h-12 items-center border-t border-line text-[15px] font-normal text-text no-underline"
              >
                {link.label}
              </Link>
            ),
          )}
        </nav>
      ) : null}
    </>
  );
}
