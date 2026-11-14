import { ModelCallTraceView } from "@/components/ModelCallTraceView";

/**
 * The admin page for one Model Call Log trace.
 *
 * @param props - `params` holds the trace's ID from the address.
 * @returns The page.
 */
export default async function AdminModelCallTracePage({
  params,
}: {
  params: Promise<{ traceId: string }>;
}) {
  const { traceId } = await params;
  return <ModelCallTraceView traceId={traceId} />;
}
