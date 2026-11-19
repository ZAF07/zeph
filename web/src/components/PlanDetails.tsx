import { secondaryButton } from "@/components/button-styles";
import { cardLink } from "@/components/card-styles";
import { CardRow } from "@/components/CardRow";
import { HomeCard } from "@/components/HomeCard";
import { PlanChoiceCard } from "@/components/PlanChoiceCard";
import { PlanSummaryCard } from "@/components/PlanSummaryCard";
import type { PlanSample } from "@/lib/design-fixtures/plan";

/**
 * The Plan page under its header: the User's plan, the plans to switch to,
 * the payment method, billing history and Cancel plan. Plans have no backend
 * yet, so the buttons do nothing.
 *
 * @param props - `plan` is what the page shows.
 * @returns The page body.
 */
export function PlanDetails({ plan }: { plan: PlanSample }) {
  return (
    <>
      <PlanSummaryCard plan={plan} />
      <div>
        <h2 className="m-0 text-[20px] font-normal text-cream">Change plan</h2>
        <p className="mt-1.5 mb-0 max-w-[600px] text-[14px] text-soft">
          Switching takes effect straight away. Nothing Zeph remembers is lost
          when you move between plans.
        </p>
      </div>
      <div className="flex flex-wrap gap-4">
        {plan.choices.map((choice, index) => (
          <PlanChoiceCard key={index} choice={choice} />
        ))}
      </div>
      <div className="flex flex-wrap items-start gap-6">
        <HomeCard
          headingId="plan-payment-heading"
          title="Payment method"
          caption={`Handled by ${plan.paymentProvider}. Zeph never sees your card number.`}
          basis="narrow"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-[15px] text-text">{plan.card}</span>
            <button type="button" className={secondaryButton}>
              Update
            </button>
          </div>
        </HomeCard>
        <HomeCard
          headingId="plan-billing-heading"
          title="Billing history"
          basis="wide"
        >
          {plan.billingHistory.map((payment, index) => (
            <CardRow key={index}>
              <span className="text-[14px] text-text">{payment.date}</span>
              <span className="text-[14px] text-soft">
                {payment.plan} · {payment.amount}
              </span>
              <a href="#" className={cardLink}>
                Receipt
              </a>
            </CardRow>
          ))}
        </HomeCard>
      </div>
      <section
        aria-labelledby="plan-cancel-heading"
        className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-t border-line pt-6"
      >
        <div className="flex-[1_1_360px]">
          <h2
            id="plan-cancel-heading"
            className="m-0 text-[17px] font-normal text-cream"
          >
            Cancel plan
          </h2>
          <p className="mt-1 mb-0 max-w-[620px] text-[14px] text-soft">
            You keep {plan.name} until {plan.renewalDate}, then move to the free
            plan. Your memories and settings stay.
          </p>
        </div>
        <button type="button" className={secondaryButton}>
          Cancel plan
        </button>
      </section>
    </>
  );
}
