import type { CopySlot, CopyTab } from "@/lib/api-client";

/** A slot a Copy search found, with the tab it lives in. */
export type CopySearchMatch = { tab: CopyTab; slot: CopySlot };

/**
 * Finds the slots, across every tab, whose saved text holds the words
 * searched for. Letter case and the spaces around the words don't matter.
 *
 * @param tabs - The Copy page's tabs in order.
 * @param query - What the Admin typed.
 * @returns The matching slots in tab and page order; none for an empty
 *   search.
 */
export function searchCopySlots(
  tabs: CopyTab[],
  query: string,
): CopySearchMatch[] {
  const words = query.trim().toLowerCase();
  if (!words) {
    return [];
  }
  return tabs.flatMap((tab) =>
    tab.slots
      .filter((slot) => slot.text.toLowerCase().includes(words))
      .map((slot) => ({ tab, slot })),
  );
}
