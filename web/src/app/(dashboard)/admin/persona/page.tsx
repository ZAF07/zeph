import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PersonaEditor } from "@/components/PersonaEditor";

/**
 * The admin Persona page.
 *
 * @returns The page.
 */
export default function AdminPersonaPage() {
  return (
    <div className="flex max-w-[1000px] flex-col gap-[30px]">
      <AdminPageHeader
        title="Persona"
        lead="Who Zeph is: voice, values and boundaries. Used by every core service. Users don’t choose a style — Zeph adapts to how each person writes."
      />
      <PersonaEditor />
    </div>
  );
}
