import { secondaryButton } from "@/components/button-styles";
import { filledPill } from "@/components/card-styles";
import { PlanIncludesList } from "@/components/PlanIncludesList";
import type { PlanChoice } from "@/lib/design-fixtures/plan";

/**
 * One plan under "Change plan": its name, price a month, what it includes
 * and a button to switch to it. The User's own plan has a cream outline, a
 * "Your plan" pill and a locked "Current plan" button.
 *
 * @param props - `choice` is the plan to draw.
 * @returns The card.
 */
export function PlanChoiceCard({ choice }: { choice: PlanChoice }) {
  return (
    <div
      className={`box-border flex min-w-0 flex-[1_1_220px] flex-col gap-2.5 rounded-card border bg-panel px-6 py-[22px] ${
        choice.isCurrent ? "border-cream" : "border-line"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="m-0 text-[20px] font-normal text-cream">
          {choice.name}
        </h3>
        {choice.isCurrent ? (
          <span className={filledPill}>Your plan</span>
        ) : null}
      </div>
      <div className="flex items-baseline gap-2 border-b border-line pb-[14px]">
        <span className="text-[30px] font-normal text-cream">
          {choice.price}
        </span>
        <span className="text-[13px] text-soft">/month</span>
      </div>
      <PlanIncludesList includes={choice.includes} />
      <button
        type="button"
        className={secondaryButton}
        disabled={choice.isCurrent}
      >
        {choice.isCurrent ? "Current plan" : "Switch to this plan"}
      </button>
    </div>
  );
}
