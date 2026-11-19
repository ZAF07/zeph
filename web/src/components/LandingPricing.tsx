import { LandingPlan, type LandingPlanDetails } from "@/components/LandingPlan";
import { SectionIntro } from "@/components/SectionIntro";
import {
  siteColumn,
  splitContent,
  splitIntro,
  splitSection,
} from "@/components/site-styles";
import { type Copy, readCopy } from "@/lib/copy";

/**
 * The plans, as drawn: the start of each plan's Copy slot keys, how many
 * lines it includes, whether it has a badge and whether its button is the
 * primary one. Billing is still to build, so every button signs up.
 */
const plans = [
  {
    slotPrefix: "pricing.free",
    features: 3,
    badge: false,
    primary: false,
  },
  {
    slotPrefix: "pricing.plus",
    features: 4,
    badge: true,
    primary: true,
  },
  {
    slotPrefix: "pricing.pro",
    features: 4,
    badge: false,
    primary: false,
  },
];

/**
 * Reads one plan's words from the Copy.
 *
 * @param copy - The website's Copy.
 * @param plan - Which plan, and how it is drawn.
 * @returns The plan to draw.
 */
function planDetails(
  copy: Copy,
  plan: (typeof plans)[number],
): LandingPlanDetails {
  const text = (part: string) => readCopy(copy, `${plan.slotPrefix}.${part}`);
  return {
    name: text("name"),
    badge: plan.badge ? text("badge") : undefined,
    blurb: text("blurb"),
    price: text("price"),
    perMonth: readCopy(copy, "pricing.per_month"),
    features: Array.from({ length: plan.features }, (_, index) =>
      text(`feature_${index + 1}`),
    ),
    action: text("button"),
    primary: plan.primary,
  };
}

/**
 * Landing's pricing section, also the Pricing page's body: the intro and
 * the three plans, worded by the Pricing slots.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The section.
 */
export function LandingPricing({ copy }: { copy: Copy }) {
  return (
    <section
      id="pricing"
      className={`${siteColumn} ${splitSection} pt-14 pb-24`}
    >
      <SectionIntro
        eyebrow={readCopy(copy, "pricing.eyebrow")}
        title={
          <>
            {readCopy(copy, "pricing.heading_first_line")}
            <br />
            {readCopy(copy, "pricing.heading_second_line")}
          </>
        }
        body={readCopy(copy, "pricing.lead")}
        className={splitIntro}
      />
      <div className={splitContent}>
        <div className="flex flex-wrap gap-y-9">
          {plans.map((plan) => (
            <LandingPlan key={plan.slotPrefix} plan={planDetails(copy, plan)} />
          ))}
        </div>
      </div>
    </section>
  );
}
