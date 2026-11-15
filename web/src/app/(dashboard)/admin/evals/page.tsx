import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalAreaTabs } from "@/components/EvalAreaTabs";
import { EvalRunsList } from "@/components/EvalRunsList";

/**
 * The admin Eval Runs page.
 *
 * @returns The page.
 */
export default function AdminEvalRunsPage() {
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="Evals"
        lead="Check how the Companion behaves with the real model. Each run uses made-up Users in its own Eval database, never real ones."
      />
      <EvalAreaTabs />
      <EvalRunsList />
    </div>
  );
}
