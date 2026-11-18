/** A link on the public pages: where it goes and its text. */
export type SiteLink = { href: string; label: string };

/** The public header's nav links, also the footer's Product column. */
export const siteNavLinks: SiteLink[] = [
  { href: "/how-it-works", label: "How It Works" },
  { href: "/#conversations", label: "Conversations" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/#faq", label: "FAQ" },
];
