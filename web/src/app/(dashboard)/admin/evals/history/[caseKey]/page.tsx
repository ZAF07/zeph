import { CaseHistoryView } from "@/components/CaseHistoryView";

/**
 * The admin page for one Eval Case's results in recent runs.
 *
 * @param props - `params` holds the case's key from the address.
 * @returns The page.
 */
export default async function AdminCaseHistoryPage({
  params,
}: {
  params: Promise<{ caseKey: string }>;
}) {
  const { caseKey } = await params;
  return <CaseHistoryView caseKey={decodeURIComponent(caseKey)} />;
}
