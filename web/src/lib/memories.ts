import type { MemoryItem } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";

/**
 * Says where a Memory Item came from and when, like "From a conversation ·
 * 2 Oct".
 *
 * @param item - The Memory Item.
 * @param timeZone - The User's time zone.
 * @returns The source line.
 */
export function memorySourceLabel(item: MemoryItem, timeZone?: string): string {
  const origin =
    item.source === "onboarding" ? "From onboarding" : "From a conversation";
  return `${origin} · ${formatShortDay(item.updated_at, timeZone)}`;
}

/** The tabs of the Memories page, in the order they are drawn. */
export const memoriesTabs = [
  { id: "memories", label: "Memories" },
  { id: "about", label: "About you" },
  { id: "threads", label: "What's going on" },
  { id: "helps", label: "What helps you" },
  { id: "summaries", label: "Conversation Summaries" },
  { id: "photos", label: "Photos" },
] as const;

/** One tab of the Memories page. */
export type MemoriesTab = (typeof memoriesTabs)[number]["id"];

/**
 * Picks the Memories tab named by a `?tab=` value.
 *
 * @param value - The `tab` query value, or null when there is none.
 * @returns That tab, or the Memories tab when the value names no tab.
 */
export function memoriesTabFromQuery(value: string | null): MemoriesTab {
  const tab = memoriesTabs.find((option) => option.id === value);
  return tab?.id ?? "memories";
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
