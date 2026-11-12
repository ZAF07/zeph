import type { KnowledgeStatus } from "@/lib/api-client";
import { knowledgeStatusLabels } from "@/lib/knowledge-labels";

/**
 * The coloured pill showing whether a Knowledge document is Ready, Pending
 * or Failed.
 *
 * @param props - `status` is the document's status.
 * @returns The pill.
 */
export function KnowledgeStatusPill({ status }: { status: KnowledgeStatus }) {
  const { label, pill } = knowledgeStatusLabels[status];
  return (
    <span
      className={`inline-flex w-fit items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium ${pill}`}
    >
      {label}
    </span>
  );
}
