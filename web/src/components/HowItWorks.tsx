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

/** The five steps, in order. */
const steps: HowItWorksStepDetails[] = [
  {
    title: "Create your account",
    tag: "About two minutes",
    text: "Sign up on this site and answer a few short questions: what to call you, what brings you here, and whether Zeph may remember things and check in on you.",
  },
  {
    title: "Connect Telegram",
    tag: "One tap",
    text: "One tap links your account to Zeph on Telegram. Every conversation happens there, so there is no new app to learn.",
  },
  {
    title: "Talk it through",
    tag: "Whenever you like",
    text: "Message Zeph the way you would message a thoughtful friend. It asks questions, listens, and disagrees when that is more useful than agreeing. It draws on philosophy, psychology and mindfulness, in plain words.",
  },
  {
    title: "It remembers, with your permission",
    tag: "Your choice",
    text: "If you allow it, Zeph keeps the details that matter, like your goals and the people you mention, so you never start from zero. You can read every memory and delete any of them.",
  },
  {
    title: "It checks in, if you want it to",
    tag: "Your choice",
    text: "Turn check-ins on and Zeph will sometimes message you first. You set how often at most and your quiet hours. Zeph chooses the moment, and sometimes stays quiet to give you space.",
  },
];

/** The Dashboard pages a User controls Zeph from. */
const dashboardCards = [
  {
    title: "Memories",
    text: "Read what Zeph remembers and delete any of it, one item or everything.",
  },
  {
    title: "Check-ins",
    text: "Change how often, set quiet hours, pause for a day or a week, or switch them off.",
  },
  {
    title: "Account & privacy",
    text: "Turn memory off, stop Zeph looking at photos, delete your data or your account.",
  },
];

/**
 * The public How It Works page, from the design's `HowItWorks` file: the
 * stepping-stones hero, the five steps, what the Dashboard controls, a
 * sign-up band and the footer.
 *
 * @returns The page.
 */
export function HowItWorks() {
  return (
    <>
      <SiteHero
        background={siteBackgrounds.howItWorksHero}
        padding="pt-14 pb-[190px] max-[899px]:pt-7 max-[899px]:pb-[340px]"
        eyebrow="How it works"
        title={
          <>
            One conversation,
            <br />
            carried through your days.
          </>
        }
      >
        <p className="m-0 max-w-[420px] text-[16px] text-text">
          You sign up here and talk to Zeph in Telegram. This site is where you
          see what it remembers and decide how it behaves. Five steps, most of
          them one tap.
        </p>
      </SiteHero>
      <section className={`${siteColumn} ${splitSection} pt-10 pb-[72px]`}>
        <SectionIntro
          eyebrow="From sign-up to check-in"
          title={
            <>
              What happens,
              <br />
              in order.
            </>
          }
          body="Steps one and two happen once. The rest is the conversation itself."
          className={splitIntro}
        />
        <ol className={`${splitContent} m-0 flex list-none flex-col p-0`}>
          {steps.map((step, index) => (
            <HowItWorksStep
              key={step.title}
              number={index + 1}
              step={step}
              last={index === steps.length - 1}
            />
          ))}
        </ol>
      </section>
      <section className={`${siteColumn} ${splitSection} pt-6 pb-[72px]`}>
        <SectionIntro
          eyebrow="Your dashboard"
          title={
            <>
              You decide
              <br />
              what Zeph keeps.
            </>
          }
          body="Everything Zeph holds about you is visible on this site, and all of it can be removed."
          className={splitIntro}
        />
        <div className={`${splitContent} flex flex-col gap-5`}>
          <div className="flex flex-wrap gap-4">
            {dashboardCards.map((card) => (
              <div
                key={card.title}
                className="box-border min-w-0 flex-[1_1_240px] rounded-card border border-line bg-panel px-[22px] py-5"
              >
                <h3 className="mt-0 mb-1.5 text-[17px] font-normal text-cream">
                  {card.title}
                </h3>
                <p className="m-0 text-[14px] text-soft">{card.text}</p>
              </div>
            ))}
          </div>
          <p className="m-0 rounded-note border border-line px-[22px] py-4 text-[14px] text-soft">
            <span className="text-text">What Zeph is not.</span> Zeph is an AI.
            It is not a therapist, a doctor or a crisis service, and it cannot
            help in an emergency.
          </p>
        </div>
      </section>
      <section className="bg-bg-deep">
        <div
          className={`${siteColumn} flex flex-wrap items-center justify-between gap-x-10 gap-y-5 border-b border-line py-14`}
        >
          <div className="min-w-0 flex-[1_1_320px]">
            <h2 className="mt-0 mb-1.5 text-[28px] leading-[1.15] font-normal text-cream">
              Ready when you are.
            </h2>
            <p className="m-0 text-soft">
              Start free. It takes about two minutes to reach your first
              conversation.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <PillLink href="/sign-up" label="Get Started Free" primary />
            <Link href="/#pricing" className={secondaryButton}>
              See pricing
            </Link>
          </div>
        </div>
      </section>
      <SiteFooter />
    </>
  );
}
