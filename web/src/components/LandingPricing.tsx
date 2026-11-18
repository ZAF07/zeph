import { LandingPlan, type LandingPlanDetails } from "@/components/LandingPlan";
import { SectionIntro } from "@/components/SectionIntro";
import {
  siteColumn,
  splitContent,
  splitIntro,
  splitSection,
} from "@/components/site-styles";

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
      className={`${siteColumn} ${splitSection} pt-14 pb-24`}
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
        className={splitIntro}
      />
      <div className={splitContent}>
        <div className="flex flex-wrap gap-y-9">
          {plans.map((plan) => (
            <LandingPlan key={plan.name} plan={plan} />
          ))}
        </div>
      </div>
    </section>
  );
}
