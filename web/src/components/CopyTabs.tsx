import { tabClass, tabRow } from "@/components/tab-styles";
import type { CopyTab } from "@/lib/api-client";

/**
 * The Copy page's row of tabs, one per website page, drawn as the Memories
 * tabs are. From 900px up it wraps; on a phone it scrolls sideways.
 *
 * @param props - `tabs` are the Copy page's tabs in order, `selected` is
 *   the key of the tab shown, and `onSelect` is called with the key of the
 *   tab the Admin chooses.
 * @returns The tab row.
 */
export function CopyTabs({
  tabs,
  selected,
  onSelect,
}: {
  tabs: CopyTab[];
  selected: string;
  onSelect: (tab: string) => void;
}) {
  return (
    <div role="tablist" aria-label="Website pages" className={tabRow}>
      {tabs.map((tab) => {
        const isSelected = tab.tab === selected;
        return (
          <button
            key={tab.tab}
            type="button"
            role="tab"
            aria-selected={isSelected}
            onClick={() => onSelect(tab.tab)}
            className={tabClass(isSelected)}
          >
            {tab.name}
          </button>
        );
      })}
    </div>
  );
}
