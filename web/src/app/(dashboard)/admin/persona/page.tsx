import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PersonaEditor } from "@/components/PersonaEditor";
import { personaTabFromQuery } from "@/lib/persona";

/**
 * The admin Persona page: the voice and the Outlook, each on its own tab.
 *
 * @param props - `searchParams` holds `tab`, which picks the tab shown first.
 * @returns The page.
 */
export default async function AdminPersonaPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string | string[] }>;
}) {
  const { tab } = await searchParams;
  return (
    <>
      <AdminPageHeader
        title="Persona"
        lead="Who Zeph is, in two texts. The voice is how it speaks. The Outlook is how it sees people. Users don’t choose a style. Zeph adapts to how each person writes."
      />
      <PersonaEditor initialTab={personaTabFromQuery(tab)} />
    </>
  );
}
