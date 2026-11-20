import type { MemoryItem } from "@/lib/api-client";
import { type Copy, fillCopy } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";

/**
 * Says where a Memory Item came from and when, like "From a conversation ·
 * 2 Oct".
 *
 * @param item - The Memory Item.
 * @param copy - The Memories page's Copy.
 * @param timeZone - The User's time zone.
 * @returns The source line.
 */
export function memorySourceLabel(
  item: MemoryItem,
  copy: Copy,
  timeZone?: string,
): string {
  const slot =
    item.source === "onboarding"
      ? "memories.items.from_onboarding"
      : "memories.items.from_conversation";
  return fillCopy(copy, slot, {
    day: formatShortDay(item.updated_at, timeZone),
  });
}

/**
 * The tabs of the Memories page, in the order they are drawn. Each tab's
 * name is the `memories.tabs.<tab>` Copy slot.
 */
export const memoriesTabs = [
  "memories",
  "about",
  "threads",
  "patterns",
  "helps",
  "summaries",
  "photos",
] as const;

/** One tab of the Memories page. */
export type MemoriesTab = (typeof memoriesTabs)[number];

/**
 * Picks the Memories tab named by a `?tab=` value.
 *
 * @param value - The `tab` query value, or null when there is none.
 * @returns That tab, or the Memories tab when the value names no tab.
 */
export function memoriesTabFromQuery(value: string | null): MemoriesTab {
  const tab = memoriesTabs.find((option) => option === value);
  return tab ?? "memories";
}

/**
 * Builds the query string for a Memories tab, keeping any other query
 * values. The Memories tab has no `tab` value.
 *
 * @param search - The current query string, such as `?design=menu-open`.
 * @param tab - The tab to show.
 * @returns The new query string, starting with `?`, or "" when empty.
 */
export function searchWithMemoriesTab(
  search: string,
  tab: MemoriesTab,
): string {
  const params = new URLSearchParams(search);
  if (tab === "memories") {
    params.delete("tab");
  } else {
    params.set("tab", tab);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}
