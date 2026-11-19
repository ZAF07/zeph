import Link from "next/link";

import { type SiteLink, siteNavLinks } from "@/components/site-links";
import { siteColumn } from "@/components/site-styles";

/**
 * The footer's link columns. Follow and Legal have no pages yet, so their
 * links go nowhere, as drawn.
 */
const footerColumns: { title: string; links: SiteLink[] }[] = [
  { title: "Product", links: siteNavLinks },
  {
    title: "Follow",
    links: [
      { href: "#", label: "Telegram" },
      { href: "#", label: "X" },
      { href: "#", label: "YouTube" },
      { href: "#", label: "Instagram" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "#", label: "Terms of Service" },
      { href: "#", label: "Privacy Policy" },
    ],
  },
];

/**
 * The footer on the public pages: the wordmark and a line, the
 * Product, Follow and Legal links, the copyright and the AI notice.
 *
 * @returns The footer.
 */
export function SiteFooter() {
  return (
    <footer className="bg-bg-deep">
      <div className={`${siteColumn} flex flex-col gap-9 pt-14 pb-7`}>
        <div className="flex flex-wrap gap-x-12 gap-y-9">
          <div className="min-w-0 flex-[2_1_260px]">
            <div className="text-[26px] font-normal text-cream">Zeph</div>
            <p className="mt-2.5 mb-0 max-w-[300px] text-[14px] text-soft">
              A thinking partner for the hours of your day, on Telegram.
            </p>
          </div>
          {footerColumns.map((column) => (
            <div
              key={column.title}
              className="flex min-w-0 flex-[1_1_140px] flex-col"
            >
              <div className="pb-1.5 text-[11px] font-medium tracking-[2px] text-mute uppercase">
                {column.title}
              </div>
              {column.links.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  className="inline-flex min-h-10 items-center text-[14px] text-text no-underline"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          ))}
        </div>
        <div className="flex flex-wrap justify-between gap-2.5 border-t border-line pt-[18px] text-[13px] text-mute">
          <span>© 2026 Zeph</span>
          <span>Zeph is an AI. It is not therapy or medical care.</span>
        </div>
      </div>
    </footer>
  );
}
