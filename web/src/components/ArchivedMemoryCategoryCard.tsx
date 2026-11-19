import { secondaryButton } from "@/components/button-styles";
import { CardCount } from "@/components/CardCount";
import { CardSaveBar } from "@/components/CardSaveBar";
import { FoldingCard } from "@/components/FoldingCard";
import type { MemoryCategoryOverview } from "@/lib/api-client";

/**
 * One archived Memory Category as a card of the card list. The folded row
 * shows its name, description and the Memory Items kept. Open, it has only
 * Restore.
 *
 * @param props - `category` is the archived category; `isOpen` and
 *   `onToggle` open and fold it; `onRestore` restores it; `isChanging`
 *   turns Restore off while a change saves.
 * @returns The card.
 */
export function ArchivedMemoryCategoryCard({
  category,
  isOpen,
  onToggle,
  onRestore,
  isChanging,
}: {
  category: MemoryCategoryOverview;
  isOpen: boolean;
  onToggle: () => void;
  onRestore: () => void;
  isChanging: boolean;
}) {
  return (
    <FoldingCard
      title={category.name}
      summary={category.description}
      meta={
        <CardCount
          count={category.item_count}
          words={category.item_count === 1 ? "item kept" : "items kept"}
        />
      }
      isDirty={false}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <CardSaveBar
        note="Zeph saves no new memories here until it is restored."
        actions={
          <button
            type="button"
            className={secondaryButton}
            disabled={isChanging}
            onClick={onRestore}
          >
            Restore
          </button>
        }
      />
    </FoldingCard>
  );
}
