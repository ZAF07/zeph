import { EvalRunView } from "@/components/EvalRunView";

/**
 * The admin page for one Eval Run.
 *
 * @param props - `params` holds the run's ID from the address.
 * @returns The page.
 */
export default async function AdminEvalRunPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  return <EvalRunView runId={runId} />;
}
