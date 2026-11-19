import { tabClass, tabRow } from "@/components/tab-styles";
import { type MemoriesTab, memoriesTabs } from "@/lib/memories";

/**
 * The Memories page's row of six tabs. From 900px up it wraps; on a phone it
 * scrolls sideways and never wraps.
 *
 * @param props - `selected` is the tab shown, and `onSelect` is called with
 *   the tab the User chooses.
 * @returns The tab row.
 */
export function MemoriesTabs({
  selected,
  onSelect,
}: {
  selected: MemoriesTab;
  onSelect: (tab: MemoriesTab) => void;
}) {
  return (
    <div role="tablist" aria-label="Memories" className={tabRow}>
      {memoriesTabs.map((option) => {
        const isSelected = option.id === selected;
        return (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={isSelected}
            onClick={() => onSelect(option.id)}
            className={tabClass(isSelected)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
