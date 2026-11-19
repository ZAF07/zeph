import { type Copy, readCopy } from "@/lib/copy";

/** A link on the public pages: where it goes and its text. */
export type SiteLink = { href: string; label: string };

/** The words of the public header, from the Copy's Shared slots. */
export type SiteHeaderWords = {
  wordmark: string;
  homeLinkLabel: string;
  navLinks: SiteLink[];
  logIn: string;
  signUp: string;
  openMenu: string;
  closeMenu: string;
  menuLabel: string;
};

/**
 * The public header's nav links, also the footer's Product column.
 *
 * @param copy - The website's Copy.
 * @returns The links in order, worded by Copy.
 */
export function siteNavLinks(copy: Copy): SiteLink[] {
  return [
    {
      href: "/how-it-works",
      label: readCopy(copy, "shared.nav.how_it_works"),
    },
    {
      href: "/#conversations",
      label: readCopy(copy, "shared.nav.conversations"),
    },
    { href: "/pricing", label: readCopy(copy, "shared.nav.pricing") },
    { href: "/#faq", label: readCopy(copy, "shared.nav.faq") },
  ];
}

/**
 * Reads the public header's words from the Copy, so the header, which runs
 * in the browser, gets only the words it shows.
 *
 * @param copy - The website's Copy.
 * @returns The header's words.
 */
export function siteHeaderWords(copy: Copy): SiteHeaderWords {
  return {
    wordmark: readCopy(copy, "shared.wordmark"),
    homeLinkLabel: readCopy(copy, "shared.header.home_link_label"),
    navLinks: siteNavLinks(copy),
    logIn: readCopy(copy, "shared.header.log_in"),
    signUp: readCopy(copy, "shared.header.sign_up_button"),
    openMenu: readCopy(copy, "shared.header.open_menu"),
    closeMenu: readCopy(copy, "shared.header.close_menu"),
    menuLabel: readCopy(copy, "shared.header.menu_label"),
  };
}
