import Link from "next/link";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { PlanIncludesList } from "@/components/PlanIncludesList";

/** One plan in Landing's pricing section. */
export type LandingPlanDetails = {
  name: string;
  badge?: string;
  blurb: string;
  price: string;
  perMonth: string;
  features: string[];
  action: string;
  primary: boolean;
};

/**
 * One plan column in Landing's pricing section: its name, a line, the price
 * a month, what it includes and a sign-up button.
 *
 * @param props - `plan` is the plan to draw.
 * @returns The plan column.
 */
export function LandingPlan({ plan }: { plan: LandingPlanDetails }) {
  return (
    <div className="box-border flex min-w-0 flex-[1_1_200px] flex-col gap-2.5 border-l border-line px-6">
      <div className="flex items-center gap-3">
        <h3 className="m-0 text-[20px] font-normal text-cream">{plan.name}</h3>
        {plan.badge ? (
          <span className="rounded-pill bg-cream px-2.5 py-0.5 text-[11px] font-medium text-ink">
            {plan.badge}
          </span>
        ) : null}
      </div>
      <p className="m-0 min-h-11 text-[14px] text-soft">{plan.blurb}</p>
      <div className="flex items-baseline gap-2 border-b border-line pb-[14px]">
        <span className="text-[34px] font-normal text-cream">{plan.price}</span>
        <span className="text-[13px] text-soft">{plan.perMonth}</span>
      </div>
      <PlanIncludesList includes={plan.features} />
      <Link
        href="/sign-up"
        className={`${plan.primary ? primaryButton : secondaryButton} box-border w-full`}
      >
        {plan.action}
      </Link>
    </div>
  );
}
