import Link from "next/link";

import { LandingConversation } from "@/components/LandingConversation";
import { LandingDay } from "@/components/LandingDay";
import { LandingFaq } from "@/components/LandingFaq";
import { LandingPricing } from "@/components/LandingPricing";
import { PillLink } from "@/components/PillLink";
import { siteBackgrounds } from "@/components/site-backgrounds";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHero } from "@/components/SiteHero";

/**
 * The page signed-out people see at `/`, from the design's `Landing` file:
 * the pavilion hero, a sample conversation, a day with Zeph, pricing, the
 * FAQ and the footer.
 *
 * @returns The page.
 */
export function Landing() {
  return (
    <>
      <SiteHero
        background={siteBackgrounds.landingHero}
        padding="pt-11 pb-[300px] max-[899px]:pt-7 max-[899px]:pb-[350px]"
        eyebrow="Your AI companion"
        title={
          <>
            Think Deeper, <br className="max-[899px]:hidden" />
            Live More Deliberately.
          </>
        }
      >
        <p className="mt-0 mb-7 max-w-[400px] text-[16px] text-text">
          A thinking partner that challenges your perspective, helps you make
          better decisions, and stays with you through the ups and downs.
        </p>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <PillLink href="/sign-up" label="Get Started Free" primary />
          <Link
            href="/how-it-works"
            className="inline-flex min-h-11 items-center gap-3 text-[14px] font-normal text-text no-underline"
          >
            <span
              aria-hidden="true"
              className="box-border flex size-[30px] items-center justify-center rounded-full border border-soft"
            >
              <svg
                width="10"
                height="12"
                viewBox="0 0 10 12"
                fill="none"
                stroke="#EAF2F3"
                strokeWidth="1.3"
                strokeLinejoin="round"
              >
                <path d="M1.5 1.5l7 4.5-7 4.5z" />
              </svg>
            </span>
            See How It Works
          </Link>
        </div>
      </SiteHero>
      <LandingConversation />
      <LandingDay />
      <LandingPricing />
      <LandingFaq />
      <SiteFooter />
    </>
  );
}
