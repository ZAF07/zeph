import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalAreaTabs } from "@/components/EvalAreaTabs";
import { EvalCostsForm } from "@/components/EvalCostsForm";

/**
 * The admin page for Model Prices and the Eval run token limit.
 *
 * @returns The page.
 */
export default function AdminEvalCostsPage() {
  return (
    <div className="flex max-w-[920px] flex-col gap-[22px]">
      <AdminPageHeader
        title="Model Prices"
        lead="What each model costs, for Eval Run estimates and totals, and the most tokens one run may use."
      />
      <EvalAreaTabs />
      <EvalCostsForm />
    </div>
  );
}
