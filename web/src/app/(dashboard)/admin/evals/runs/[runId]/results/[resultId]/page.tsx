import { CaseResultTraceView } from "@/components/CaseResultTraceView";

/**
 * The admin page for one Case Result's full trace.
 *
 * @param props - `params` holds the run's and the result's IDs from the
 *   address.
 * @returns The page.
 */
export default async function AdminCaseResultTracePage({
  params,
}: {
  params: Promise<{ runId: string; resultId: string }>;
}) {
  const { runId, resultId } = await params;
  return <CaseResultTraceView runId={runId} resultId={resultId} />;
}
