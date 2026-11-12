import { KnowledgeDocumentView } from "@/components/KnowledgeDocumentView";

/**
 * The admin page for one Knowledge document.
 *
 * @param props - `params` holds the document's ID from the address.
 * @returns The page.
 */
export default async function AdminKnowledgeDocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <KnowledgeDocumentView documentId={id} />;
}
