import { AdminPageHeader } from "@/components/AdminPageHeader";
import { ThoughtExperimentsManager } from "@/components/ThoughtExperimentsManager";

/**
 * The admin Thought Experiments page: made-up situations that tell two
 * look-alike Pattern Types apart.
 *
 * @returns The page.
 */
export default function AdminThoughtExperimentsPage() {
  return (
    <>
      <AdminPageHeader
        title="Thought Experiments"
        lead="Made-up situations, each telling two look-alike Pattern Types apart. Zeph asks one when a User’s stories don’t show which of the two it is. They can’t be deleted, because past tries name them: archive one instead."
      />
      <ThoughtExperimentsManager />
    </>
  );
}
