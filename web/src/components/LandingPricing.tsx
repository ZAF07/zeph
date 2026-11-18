import { LandingPlan, type LandingPlanDetails } from "@/components/LandingPlan";
import { SectionIntro } from "@/components/SectionIntro";
import { siteColumn } from "@/components/site-links";

/** The plans, as drawn. Billing is still to build, so every button signs up. */
const plans: LandingPlanDetails[] = [
  {
    name: "Free",
    blurb: "Start your journey with Zeph.",
    price: "S$0",
    features: [
      "Thoughtful conversations",
      "Basic daily check-ins",
      "Core reflection prompts",
    ],
    action: "Get Started",
    primary: false,
  },
  {
    name: "Plus",
    badge: "Most Popular",
    blurb: "A proactive companion for real progress.",
    price: "S$12",
    features: [
      "Everything in Free",
      "Proactive check-ins throughout the day",
      "Goal and habit support",
      "Longer memory and context",
    ],
    action: "Start Plus",
    primary: true,
  },
  {
    name: "Pro",
    blurb: "A more personalized and ongoing partnership.",
    price: "S$19",
    features: [
      "Everything in Plus",
      "Deeper long-term insights",
      "Custom routines and focus areas",
      "Early access to new features",
    ],
    action: "Start Pro",
    primary: false,
  },
];

/**
 * Landing's pricing section: the intro and the three plans.
 *
 * @returns The section.
 */
export function LandingPricing() {
  return (
    <section
      id="pricing"
      className={`${siteColumn} flex flex-wrap items-start gap-x-14 gap-y-9 pt-14 pb-24`}
    >
      <SectionIntro
        eyebrow="Pricing"
        title={
          <>
            Simple plans
            <br />
            that grow with you.
          </>
        }
        body="Start free, upgrade when you are ready for deeper support."
        className="max-w-[340px] min-w-0 flex-[1_1_280px]"
      />
      <div className="min-w-0 flex-[999_1_560px]">
        <div className="flex flex-wrap gap-y-9">
          {plans.map((plan) => (
            <LandingPlan key={plan.name} plan={plan} />
          ))}
        </div>
      </div>
    </section>
  );
}
