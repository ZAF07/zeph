"use client";

import type { ReactNode } from "react";

import { CardListToolbar } from "@/components/CardListToolbar";
import { useOpenCards } from "@/lib/use-open-cards";

/** How a card opens and folds, handed to each card. */
export type CardFolding = { isOpen: boolean; onToggle: () => void };

/**
 * The card-list template's list: the toolbar (count, Expand all, Collapse
 * all, Add), anything shown above the cards (such as the add box), then
 * the cards. The first card starts open.
 *
 * @param props - `items` are the things listed, in order; `count` is the
 *   toolbar's count line; `addLabel`, `onAdd` and `isAddDisabled` are the
 *   add button; `aboveList` goes between the toolbar and the cards;
 *   `renderCard` draws one card from its item, place and folding.
 * @returns The toolbar and the cards.
 */
export function CardList<Item extends { id: string }>({
  items,
  count,
  addLabel,
  onAdd,
  isAddDisabled = false,
  aboveList,
  renderCard,
}: {
  items: Item[];
  count: ReactNode;
  addLabel?: string;
  onAdd?: () => void;
  isAddDisabled?: boolean;
  aboveList?: ReactNode;
  renderCard: (item: Item, index: number, folding: CardFolding) => ReactNode;
}) {
  const openCards = useOpenCards(items.map((item) => item.id));
  return (
    <>
      <CardListToolbar
        count={count}
        onExpandAll={openCards.expandAll}
        onCollapseAll={openCards.collapseAll}
        addLabel={addLabel}
        onAdd={onAdd}
        isAddDisabled={isAddDisabled}
      />
      {aboveList}
      {items.length > 0 ? (
        <div className="flex flex-col gap-3">
          {items.map((item, index) =>
            renderCard(item, index, {
              isOpen: openCards.isOpen(item.id),
              onToggle: () => openCards.toggle(item.id),
            }),
          )}
        </div>
      ) : null}
    </>
  );
}
