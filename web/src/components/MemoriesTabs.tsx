import { type MemoriesTab, memoriesTabs } from "@/lib/memories";

const tabBase =
  "min-h-11 flex-none cursor-pointer border-0 border-b-2 bg-transparent px-0.5 text-[14px] whitespace-nowrap min-[900px]:flex-initial";

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
    <div
      role="tablist"
      aria-label="Memories"
      className="flex flex-nowrap gap-x-[22px] gap-y-1 overflow-x-auto border-b border-line min-[900px]:flex-wrap min-[900px]:gap-x-5 min-[900px]:overflow-x-visible"
    >
      {memoriesTabs.map((option) => {
        const isSelected = option.id === selected;
        return (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={isSelected}
            onClick={() => onSelect(option.id)}
            className={`${tabBase} ${
              isSelected
                ? "border-cream font-normal text-cream"
                : "border-transparent font-light text-soft"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
