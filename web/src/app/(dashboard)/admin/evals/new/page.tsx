import { AdminPageHeader } from "@/components/AdminPageHeader";
import { NewEvalRunForm } from "@/components/NewEvalRunForm";

/**
 * The admin page for starting an Eval Run.
 *
 * @returns The page.
 */
export default function AdminNewEvalRunPage() {
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="New Eval Run"
        lead="Pick the Evals to run with the live Platform Settings. Results appear on the run’s page as each case finishes."
      />
      <NewEvalRunForm />
    </div>
  );
}
