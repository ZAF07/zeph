import Link from "next/link";

import { secondaryButton } from "@/components/button-styles";
import {
  HowItWorksStep,
  type HowItWorksStepDetails,
} from "@/components/HowItWorksStep";
import { PillLink } from "@/components/PillLink";
import { SectionIntro } from "@/components/SectionIntro";
import { siteBackgrounds } from "@/components/site-backgrounds";
import {
  siteColumn,
  splitContent,
  splitIntro,
  splitSection,
} from "@/components/site-styles";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHero } from "@/components/SiteHero";
import { type Copy, readCopy } from "@/lib/copy";

/** The Copy slot key prefixes of the steps, in order. */
const stepSlotPrefixes = [
  "how_it_works.steps.step_1",
  "how_it_works.steps.step_2",
  "how_it_works.steps.step_3",
  "how_it_works.steps.step_4",
  "how_it_works.steps.step_5",
];

/** The Copy slot key prefixes of the Dashboard cards, in order. */
const dashboardCardSlotPrefixes = [
  "how_it_works.dashboard.memories",
  "how_it_works.dashboard.check_ins",
  "how_it_works.dashboard.account",
];

/**
 * Reads the steps' words from the Copy.
 *
 * @param copy - The website's Copy.
 * @returns The five steps in order.
 */
function stepDetails(copy: Copy): HowItWorksStepDetails[] {
  return stepSlotPrefixes.map((slotPrefix) => {
    const slot = (part: string) => readCopy(copy, `${slotPrefix}.${part}`);
    return { title: slot("title"), tag: slot("tag"), text: slot("text") };
  });
}

/**
 * The public How It Works page, from the design's `HowItWorks` file: the
 * stepping-stones hero, the five steps, what the Dashboard controls, a
 * sign-up band and the footer. Every word comes from Copy: the How it
 * works slots, and the Shared ones for the header and footer.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The page.
 */
export function HowItWorks({ copy }: { copy: Copy }) {
  const text = (key: string) => readCopy(copy, `how_it_works.${key}`);
  const steps = stepDetails(copy);
  return (
    <>
      <SiteHero
        copy={copy}
        background={siteBackgrounds.howItWorksHero}
        padding="pt-14 pb-[190px] max-[899px]:pt-7 max-[899px]:pb-[340px]"
        eyebrow={text("hero.eyebrow")}
        title={
          <>
            {text("hero.heading_first_line")}
            <br />
            {text("hero.heading_second_line")}
          </>
        }
      >
        <p className="m-0 max-w-[420px] text-[16px] text-text">
          {text("hero.lead")}
        </p>
      </SiteHero>
      <section className={`${siteColumn} ${splitSection} pt-10 pb-[72px]`}>
        <SectionIntro
          eyebrow={text("steps.eyebrow")}
          title={
            <>
              {text("steps.heading_first_line")}
              <br />
              {text("steps.heading_second_line")}
            </>
          }
          body={text("steps.lead")}
          className={splitIntro}
        />
        <ol className={`${splitContent} m-0 flex list-none flex-col p-0`}>
          {steps.map((step, index) => (
            <HowItWorksStep
              key={index}
              number={index + 1}
              step={step}
              last={index === steps.length - 1}
            />
          ))}
        </ol>
      </section>
      <section className={`${siteColumn} ${splitSection} pt-6 pb-[72px]`}>
        <SectionIntro
          eyebrow={text("dashboard.eyebrow")}
          title={
            <>
              {text("dashboard.heading_first_line")}
              <br />
              {text("dashboard.heading_second_line")}
            </>
          }
          body={text("dashboard.lead")}
          className={splitIntro}
        />
        <div className={`${splitContent} flex flex-col gap-5`}>
          <div className="flex flex-wrap gap-4">
            {dashboardCardSlotPrefixes.map((slotPrefix) => (
              <div
                key={slotPrefix}
                className="box-border min-w-0 flex-[1_1_240px] rounded-card border border-line bg-panel px-[22px] py-5"
              >
                <h3 className="mt-0 mb-1.5 text-[17px] font-normal text-cream">
                  {readCopy(copy, `${slotPrefix}.title`)}
                </h3>
                <p className="m-0 text-[14px] text-soft">
                  {readCopy(copy, `${slotPrefix}.text`)}
                </p>
              </div>
            ))}
          </div>
          <p className="m-0 rounded-note border border-line px-[22px] py-4 text-[14px] text-soft">
            <span className="text-text">{text("dashboard.not_title")}</span>{" "}
            {text("dashboard.not_text")}
          </p>
        </div>
      </section>
      <section className="bg-bg-deep">
        <div
          className={`${siteColumn} flex flex-wrap items-center justify-between gap-x-10 gap-y-5 border-b border-line py-14`}
        >
          <div className="min-w-0 flex-[1_1_320px]">
            <h2 className="mt-0 mb-1.5 text-[28px] leading-[1.15] font-normal text-cream">
              {text("ready.heading")}
            </h2>
            <p className="m-0 text-soft">{text("ready.text")}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <PillLink
              href="/sign-up"
              label={text("ready.sign_up_button")}
              primary
            />
            <Link href="/pricing" className={secondaryButton}>
              {text("ready.pricing_link")}
            </Link>
          </div>
        </div>
      </section>
      <SiteFooter copy={copy} />
    </>
  );
}
