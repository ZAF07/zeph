import { notFound } from "next/navigation";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalAreaTabs } from "@/components/EvalAreaTabs";
import { EvalCaseEditor } from "@/components/EvalCaseEditor";
import { evalDetails, toEvalName } from "@/lib/evals";

/**
 * The admin page for editing one Eval Case.
 *
 * @param props - `params` holds the Eval's name and the case's key from
 *   the address.
 * @returns The page.
 */
export default async function AdminEditEvalCasePage({
  params,
}: {
  params: Promise<{ eval: string; key: string }>;
}) {
  const { eval: evalParam, key } = await params;
  const evalName = toEvalName(evalParam);
  if (evalName === null) {
    notFound();
  }
  const caseKey = decodeURIComponent(key);
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title={caseKey}
        lead={`A ${evalDetails[evalName].label} case. ${evalDetails[evalName].checks}`}
      />
      <EvalAreaTabs />
      <EvalCaseEditor evalName={evalName} caseKey={caseKey} />
    </div>
  );
}
