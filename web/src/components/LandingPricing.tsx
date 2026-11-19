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
  { slot: "landing.pricing.free", features: 3, badge: false, primary: false },
  { slot: "landing.pricing.plus", features: 4, badge: true, primary: true },
  { slot: "landing.pricing.pro", features: 4, badge: false, primary: false },
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
  const text = (part: string) => readCopy(copy, `${plan.slot}.${part}`);
  return {
    name: text("name"),
    badge: plan.badge ? text("badge") : undefined,
    blurb: text("blurb"),
    price: text("price"),
    perMonth: readCopy(copy, "landing.pricing.per_month"),
    features: Array.from({ length: plan.features }, (_, index) =>
      text(`feature_${index + 1}`),
    ),
    action: text("button"),
    primary: plan.primary,
  };
}

/**
 * Landing's pricing section: the intro and the three plans.
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
        eyebrow={readCopy(copy, "landing.pricing.eyebrow")}
        title={
          <>
            {readCopy(copy, "landing.pricing.heading_first_line")}
            <br />
            {readCopy(copy, "landing.pricing.heading_second_line")}
          </>
        }
        body={readCopy(copy, "landing.pricing.lead")}
        className={splitIntro}
      />
      <div className={splitContent}>
        <div className="flex flex-wrap gap-y-9">
          {plans.map((plan) => (
            <LandingPlan key={plan.slot} plan={planDetails(copy, plan)} />
          ))}
        </div>
      </div>
    </section>
  );
}
