import type { ReactNode } from "react";

import {
  type HeroBackground,
  heroBackgrounds,
} from "@/components/hero-backgrounds";

/**
 * The illustrated banner at the top of a Dashboard page: a small label, the
 * page title, one line under it, and the page's main actions at the foot.
 *
 * @param props - `background` picks the page's illustration, `eyebrow` is
 *   the small label, `title` the page title, `body` the line under it and
 *   `actions` the optional buttons at the foot.
 * @returns The banner.
 */
export function PageHero({
  background,
  eyebrow,
  title,
  body,
  actions,
}: {
  background: HeroBackground;
  eyebrow: string;
  title: string;
  body: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div
      className={`box-border flex flex-col items-start rounded-banner border border-line px-5 pt-[22px] pb-5 min-[900px]:px-[30px] min-[900px]:pt-7 min-[900px]:pb-6 ${heroBackgrounds[background]}`}
    >
      <div className="max-w-[460px]">
        <div className="flex items-center gap-3 text-[11px] font-medium tracking-[2.5px] text-soft uppercase">
          <span aria-hidden="true" className="h-px w-[18px] bg-soft" />
          {eyebrow}
        </div>
        <h1 className="mt-[14px] mb-2 text-[28px] leading-[1.15] font-normal text-cream min-[900px]:text-[32px]">
          {title}
        </h1>
        <p className="m-0 text-[14px] text-text">{body}</p>
      </div>
      {actions ? (
        <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2.5 pt-[22px]">
          {actions}
        </div>
      ) : null}
    </div>
  );
}
