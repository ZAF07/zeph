import type { PlanSample } from "@/lib/design-fixtures/plan";

/**
 * The card at the top of the Plan page: the User's plan, its price and
 * renewal day, and how many of today's messages are used, with a bar.
 *
 * @param props - `plan` is what the page shows.
 * @returns The card.
 */
export function PlanSummaryCard({ plan }: { plan: PlanSample }) {
  return (
    <div className="box-border rounded-card border border-line bg-panel px-6 py-[22px]">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-[14px]">
        <div className="min-w-0 flex-[1_1_280px]">
          <div>
            <span className="text-[26px] font-normal text-cream">
              {plan.name}
            </span>
            <span className="text-[14px] text-soft">
              {" "}
              · {plan.price} /month
            </span>
          </div>
          <p className="mt-1 mb-0 text-[14px] text-soft">
            Renews on {plan.renewalDate}.
          </p>
        </div>
        <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-2">
          <div className="flex justify-between gap-3 text-[13px] text-soft">
            <span>Messages today</span>
            <span className="text-text">
              {plan.messagesToday} of {plan.dailyLimit}
            </span>
          </div>
          <div
            role="img"
            aria-label="Messages used today"
            className="h-1.5 rounded-[3px] bg-line"
          >
            <span
              className="block h-full rounded-[3px] bg-cream"
              style={{ width: `${plan.messagesUsedPercent}%` }}
            />
          </div>
          <span className="text-[12px] text-soft">
            Resets at midnight, your time.
          </span>
        </div>
      </div>
    </div>
  );
}
