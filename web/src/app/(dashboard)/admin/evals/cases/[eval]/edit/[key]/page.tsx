import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { cardLink } from "@/components/card-styles";
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
    <>
      <Link
        href={`/admin/evals/cases/${evalName}`}
        className={`${cardLink} w-fit`}
      >
        ← {evalDetails[evalName].label} cases
      </Link>
      <AdminPageHeader
        title={caseKey}
        lead={`A ${evalDetails[evalName].label} case. ${evalDetails[evalName].checks}`}
      />
      <EvalCaseEditor evalName={evalName} caseKey={caseKey} />
    </>
  );
}
