import type { ReactNode } from "react";

import { Eyebrow } from "@/components/Eyebrow";
import { siteColumn } from "@/components/site-styles";
import { siteHeaderWords } from "@/components/site-links";
import { SiteHeader } from "@/components/SiteHeader";
import type { Copy } from "@/lib/copy";

/**
 * The illustrated top of a public page: the header, then the eyebrow, the
 * page heading and what follows it.
 *
 * @param props - `copy` is the website's Copy, for the header;
 *   `background` is the illustration's classes, `padding` the
 *   space around the text, `eyebrow` the small label, `title` the heading
 *   and `children` the line and actions under it.
 * @returns The hero.
 */
export function SiteHero({
  copy,
  background,
  padding,
  eyebrow,
  title,
  children,
}: {
  copy: Copy;
  background: string;
  padding: string;
  eyebrow: string;
  title: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className={background}>
      <SiteHeader words={siteHeaderWords(copy)} />
      <section className={`${siteColumn} ${padding}`}>
        <div className="max-w-[480px]">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h1 className="my-[18px] text-[clamp(36px,4.2vw,50px)] leading-[1.12] font-normal tracking-[-0.5px] text-cream max-[899px]:text-[34px]">
            {title}
          </h1>
          {children}
        </div>
      </section>
    </div>
  );
}
