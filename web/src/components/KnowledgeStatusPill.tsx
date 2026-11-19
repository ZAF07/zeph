import { CardTag } from "@/components/CardTag";
import type { KnowledgeStatus } from "@/lib/api-client";
import { knowledgeStatusLabels } from "@/lib/knowledge-labels";

/**
 * The tag showing whether a Knowledge document is Ready, Pending or Failed,
 * drawn as the card list's tag.
 *
 * @param props - `status` is the document's status.
 * @returns The tag.
 */
export function KnowledgeStatusPill({ status }: { status: KnowledgeStatus }) {
  const { label, tone } = knowledgeStatusLabels[status];
  return <CardTag tone={tone}>{label}</CardTag>;
}
