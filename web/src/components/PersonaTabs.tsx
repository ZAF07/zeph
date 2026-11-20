import { tabClass, tabRow } from "@/components/tab-styles";
import { type PersonaTab, personaTabs } from "@/lib/persona";

/**
 * The Persona page's row of two tabs, Voice and Outlook, drawn like the
 * Memories tabs but with the underline below the 44px tab, as the Persona
 * design draws it.
 *
 * @param props - `selected` is the tab shown, and `onSelect` is called with
 *   the tab the Admin chooses.
 * @returns The tab row.
 */
export function PersonaTabs({
  selected,
  onSelect,
}: {
  selected: PersonaTab;
  onSelect: (tab: PersonaTab) => void;
}) {
  return (
    <div role="tablist" aria-label="Persona" className={tabRow}>
      {personaTabs.map((option) => {
        const isSelected = option.tab === selected;
        return (
          <button
            key={option.tab}
            type="button"
            role="tab"
            aria-selected={isSelected}
            onClick={() => onSelect(option.tab)}
            className={`box-content ${tabClass(isSelected)}`}
          >
            {option.name}
          </button>
        );
      })}
    </div>
  );
}
