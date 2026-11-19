import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PersonaEditor } from "@/components/PersonaEditor";

/**
 * The admin Persona page.
 *
 * @returns The page.
 */
export default function AdminPersonaPage() {
  return (
    <>
      <AdminPageHeader
        title="Persona"
        lead="Who Zeph is: voice, values and boundaries. Used by every core service. Users don’t choose a style. Zeph adapts to how each person writes."
      />
      <PersonaEditor />
    </>
  );
}
