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
