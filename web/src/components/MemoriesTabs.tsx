import { tabClass, tabRow } from "@/components/tab-styles";
import { type Copy, readCopy } from "@/lib/copy";
import { type MemoriesTab, memoriesTabs } from "@/lib/memories";

/**
 * The Memories page's row of seven tabs. From 900px up it wraps; on a phone it
 * scrolls sideways and never wraps.
 *
 * @param props - `copy` holds the tab names, `selected` is the tab shown,
 *   and `onSelect` is called with the tab the User chooses.
 * @returns The tab row.
 */
export function MemoriesTabs({
  copy,
  selected,
  onSelect,
}: {
  copy: Copy;
  selected: MemoriesTab;
  onSelect: (tab: MemoriesTab) => void;
}) {
  return (
    <div
      role="tablist"
      aria-label={readCopy(copy, "memories.tabs.label")}
      className={tabRow}
    >
      {memoriesTabs.map((option) => {
        const isSelected = option === selected;
        return (
          <button
            key={option}
            type="button"
            role="tab"
            aria-selected={isSelected}
            onClick={() => onSelect(option)}
            className={tabClass(isSelected)}
          >
            {readCopy(copy, `memories.tabs.${option}`)}
          </button>
        );
      })}
    </div>
  );
}
