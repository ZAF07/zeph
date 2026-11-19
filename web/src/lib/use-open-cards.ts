"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { hasDesignFlag } from "@/lib/design-flags";

/** Which cards of a card list are open, and the ways to change that. */
export type OpenCards = {
  isOpen: (id: string) => boolean;
  toggle: (id: string) => void;
  expandAll: () => void;
  collapseAll: () => void;
};

/**
 * Tracks which cards of a card list are open. The first card starts open,
 * or none with `?design=all-folded` in fixture mode. Several can be open
 * at once.
 *
 * @param ids - Every card's id, in order.
 * @returns The open cards and the ways to change them.
 */
export function useOpenCards(ids: string[]): OpenCards {
  const allFolded = hasDesignFlag(useSearchParams(), "all-folded");
  const [openIds, setOpenIds] = useState<ReadonlySet<string>>(
    () => new Set(allFolded ? [] : ids.slice(0, 1)),
  );

  function toggle(id: string) {
    setOpenIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return {
    isOpen: (id) => openIds.has(id),
    toggle,
    expandAll: () => setOpenIds(new Set(ids)),
    collapseAll: () => setOpenIds(new Set()),
  };
}
