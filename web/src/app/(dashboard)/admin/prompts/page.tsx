import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PromptsAndModels } from "@/components/PromptsAndModels";

/**
 * The admin Prompts & models page.
 *
 * @returns The page.
 */
export default function AdminPromptsPage() {
  return (
    <div className="flex flex-col gap-[30px]">
      <AdminPageHeader
        title="Prompts & models"
        lead="One card per core service. Each prompt is combined with the Persona at runtime."
      />
      <PromptsAndModels />
    </div>
  );
}
