/** A link on the public pages: where it goes and its text. */
export type SiteLink = { href: string; label: string };

/** The public header's nav links, also the footer's Product column. */
export const siteNavLinks: SiteLink[] = [
  { href: "/how-it-works", label: "How It Works" },
  { href: "/#conversations", label: "Conversations" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/#faq", label: "FAQ" },
];

/**
 * The page width and side gutter every block of the public pages shares:
 * 1160px wide, 32px gutters, 20px below 900px.
 */
export const siteColumn =
  "mx-auto box-border max-w-[1160px] px-8 max-[899px]:px-5";
