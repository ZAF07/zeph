import Link from "next/link";

import { type SiteLink, siteNavLinks } from "@/components/site-links";
import { siteColumn } from "@/components/site-styles";
import { type Copy, readCopy } from "@/lib/copy";

/**
 * The footer's link columns, worded by Copy. Follow and Legal have no
 * pages yet, so their links go nowhere, as drawn.
 *
 * @param copy - The website's Copy.
 * @returns The columns in order, each with its title and links.
 */
function footerColumns(copy: Copy): { title: string; links: SiteLink[] }[] {
  const text = (key: string) => readCopy(copy, `shared.footer.${key}`);
  return [
    { title: text("product_title"), links: siteNavLinks(copy) },
    {
      title: text("follow_title"),
      links: [
        { href: "#", label: text("follow_telegram") },
        { href: "#", label: text("follow_x") },
        { href: "#", label: text("follow_youtube") },
        { href: "#", label: text("follow_instagram") },
      ],
    },
    {
      title: text("legal_title"),
      links: [
        { href: "#", label: text("terms") },
        { href: "#", label: text("privacy") },
      ],
    },
  ];
}

/**
 * The footer on the public pages: the wordmark and a line, the
 * Product, Follow and Legal links, the copyright and the AI notice. Every
 * word comes from the Copy's Shared slots.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The footer.
 */
export function SiteFooter({ copy }: { copy: Copy }) {
  return (
    <footer className="bg-bg-deep">
      <div className={`${siteColumn} flex flex-col gap-9 pt-14 pb-7`}>
        <div className="flex flex-wrap gap-x-12 gap-y-9">
          <div className="min-w-0 flex-[2_1_260px]">
            <div className="text-[26px] font-normal text-cream">
              {readCopy(copy, "shared.wordmark")}
            </div>
            <p className="mt-2.5 mb-0 max-w-[300px] text-[14px] text-soft">
              {readCopy(copy, "shared.footer.line")}
            </p>
          </div>
          {footerColumns(copy).map((column) => (
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
          <span>{readCopy(copy, "shared.footer.copyright")}</span>
          <span>{readCopy(copy, "shared.footer.ai_notice")}</span>
        </div>
      </div>
    </footer>
  );
}
