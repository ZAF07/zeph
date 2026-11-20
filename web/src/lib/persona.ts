/** The Persona page's two tabs: its voice and its Outlook. */
export type PersonaTab = "voice" | "outlook";

/** The Platform Setting each Persona tab edits. */
export type PersonaSettingKey = "persona" | "persona_outlook";

/** What each Persona tab edits, and the words around its editor. */
export type PersonaTabDetails = {
  tab: PersonaTab;
  name: string;
  settingKey: PersonaSettingKey;
  editorLabel: string;
  saveLabel: string;
  savedNote: string;
  idleNote: string;
};

/** The Persona tabs, by tab. */
const personaTabsByTab: Record<PersonaTab, PersonaTabDetails> = {
  voice: {
    tab: "voice",
    name: "Voice",
    settingKey: "persona",
    editorLabel: "Voice text",
    saveLabel: "Save voice",
    savedNote: "Saved. Zeph uses it from the next message.",
    idleNote: "Changes apply to the next message after saving.",
  },
  outlook: {
    tab: "outlook",
    name: "Outlook",
    settingKey: "persona_outlook",
    editorLabel: "Outlook text",
    saveLabel: "Save Outlook",
    savedNote: "Saved. Zeph uses it from the next reply.",
    idleNote: "Changes apply to the next reply after saving.",
  },
};

/** The Persona tabs, in the order they are shown. */
export const personaTabs: PersonaTabDetails[] = [
  personaTabsByTab.voice,
  personaTabsByTab.outlook,
];

/**
 * Finds what a Persona tab edits.
 *
 * @param tab - The tab.
 * @returns Its setting key and the words around its editor.
 */
export function personaTabDetails(tab: PersonaTab): PersonaTabDetails {
  return personaTabsByTab[tab];
}

/**
 * Reads the Persona tab from the page's `tab` query value.
 *
 * @param value - The `tab` value, or null when there is none.
 * @returns The tab it names; Voice for anything else.
 */
export function personaTabFromQuery(
  value: string | string[] | null | undefined,
): PersonaTab {
  return value === "outlook" ? "outlook" : "voice";
}

/**
 * Builds the query string for a Persona tab, keeping any other query
 * values. The Voice tab has no `tab` value.
 *
 * @param search - The current query string, such as `?design=menu-open`.
 * @param tab - The tab to show.
 * @returns The new query string, starting with `?`, or "" when empty.
 */
export function searchWithPersonaTab(search: string, tab: PersonaTab): string {
  const params = new URLSearchParams(search);
  if (tab === "voice") {
    params.delete("tab");
  } else {
    params.set("tab", tab);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}
