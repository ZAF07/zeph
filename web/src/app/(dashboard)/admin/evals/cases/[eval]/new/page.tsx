import { notFound } from "next/navigation";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalAreaTabs } from "@/components/EvalAreaTabs";
import { EvalCaseEditor } from "@/components/EvalCaseEditor";
import { evalDetails, toEvalName } from "@/lib/evals";

/**
 * The admin page for adding a case to an Eval.
 *
 * @param props - `params` holds the Eval's name from the address.
 * @returns The page.
 */
export default async function AdminNewEvalCasePage({
  params,
}: {
  params: Promise<{ eval: string }>;
}) {
  const evalName = toEvalName((await params).eval);
  if (evalName === null) {
    notFound();
  }
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title={`New ${evalDetails[evalName].label} case`}
        lead={evalDetails[evalName].checks}
      />
      <EvalAreaTabs />
      <EvalCaseEditor evalName={evalName} />
    </div>
  );
}
