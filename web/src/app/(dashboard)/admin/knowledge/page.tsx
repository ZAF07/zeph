import { AdminPageHeader } from "@/components/AdminPageHeader";
import { KnowledgeLibrary } from "@/components/KnowledgeLibrary";

/**
 * The admin Knowledge page: the curated library Zeph draws on.
 *
 * @returns The page.
 */
export default function AdminKnowledgePage() {
  return (
    <div className="flex flex-col gap-9">
      <AdminPageHeader
        title="Knowledge"
        lead="The curated library Zeph draws on. Documents are split and indexed after upload; only “Ready” documents are used."
      />
      <KnowledgeLibrary />
    </div>
  );
}
