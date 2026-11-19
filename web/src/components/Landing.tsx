import Link from "next/link";

import { LandingConversation } from "@/components/LandingConversation";
import { LandingDay } from "@/components/LandingDay";
import { LandingFaq } from "@/components/LandingFaq";
import { LandingPricing } from "@/components/LandingPricing";
import { PillLink } from "@/components/PillLink";
import { siteBackgrounds } from "@/components/site-backgrounds";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHero } from "@/components/SiteHero";
import { type Copy, readCopy } from "@/lib/copy";

/**
 * The page signed-out people see at `/`, from the design's `Landing` file:
 * the pavilion hero, a sample conversation, a day with Zeph, pricing, the
 * FAQ and the footer. Every word comes from the Copy's Landing slots.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The page.
 */
export function Landing({ copy }: { copy: Copy }) {
  return (
    <>
      <SiteHero
        background={siteBackgrounds.landingHero}
        padding="pt-11 pb-[300px] max-[899px]:pt-7 max-[899px]:pb-[350px]"
        eyebrow={readCopy(copy, "landing.hero.eyebrow")}
        title={
          <>
            {readCopy(copy, "landing.hero.heading_first_line")}{" "}
            <br className="max-[899px]:hidden" />
            {readCopy(copy, "landing.hero.heading_second_line")}
          </>
        }
      >
        <p className="mt-0 mb-7 max-w-[400px] text-[16px] text-text">
          {readCopy(copy, "landing.hero.lead")}
        </p>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <PillLink
            href="/sign-up"
            label={readCopy(copy, "landing.hero.sign_up_button")}
            primary
          />
          <Link
            href="/how-it-works"
            className="inline-flex min-h-11 items-center gap-3 text-[14px] font-normal text-text no-underline"
          >
            <span
              aria-hidden="true"
              className="box-border flex size-[30px] items-center justify-center rounded-full border border-soft text-text"
            >
              <svg
                width="10"
                height="12"
                viewBox="0 0 10 12"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinejoin="round"
              >
                <path d="M1.5 1.5l7 4.5-7 4.5z" />
              </svg>
            </span>
            {readCopy(copy, "landing.hero.how_it_works_link")}
          </Link>
        </div>
      </SiteHero>
      <LandingConversation copy={copy} />
      <LandingDay copy={copy} />
      <LandingPricing copy={copy} />
      <LandingFaq copy={copy} />
      <SiteFooter />
    </>
  );
}
