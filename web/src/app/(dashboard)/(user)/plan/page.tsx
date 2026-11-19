import { PageHeader } from "@/components/PageHeader";
import { PlanDetails } from "@/components/PlanDetails";
import { ToBuildTag } from "@/components/ToBuildTag";
import { planSample } from "@/lib/design-fixtures/plan";

/**
 * The Plan page, where a User will see and change their plan. Plans have no
 * backend yet, so it shows the drawn sample values with the "To build" tag
 * and makes no backend calls.
 *
 * @returns The page.
 */
export default function PlanPage() {
  return (
    <>
      <PageHeader
        eyebrow="Plan"
        title={
          <>
            Plan
            <ToBuildTag />
          </>
        }
        lead="What you are on, what it includes and how you are billed."
      />
      <PlanDetails plan={planSample} />
    </>
  );
}
