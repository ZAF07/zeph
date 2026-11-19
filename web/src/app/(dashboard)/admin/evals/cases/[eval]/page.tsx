import { notFound } from "next/navigation";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalAreaTabs } from "@/components/EvalAreaTabs";
import { EvalCasesList } from "@/components/EvalCasesList";
import { toEvalName } from "@/lib/evals";

/**
 * The admin page listing one Eval's cases.
 *
 * @param props - `params` holds the Eval's name from the address.
 * @returns The page.
 */
export default async function AdminEvalCasesForEvalPage({
  params,
}: {
  params: Promise<{ eval: string }>;
}) {
  const evalName = toEvalName((await params).eval);
  if (evalName === null) {
    notFound();
  }
  return (
    <>
      <AdminPageHeader
        title="Eval Cases"
        lead="The situations each Eval checks. Edits apply from the next run; past runs keep each case as it was. Edits never go back to the seed files."
      />
      <EvalAreaTabs />
      <EvalCasesList evalName={evalName} />
    </>
  );
}
