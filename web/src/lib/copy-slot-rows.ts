import type { CopySlot } from "@/lib/api-client";
import { countSlotEndings } from "@/lib/copy";

/**
 * Lays a Copy tab's slots out in rows, so text that changes with a number
 * shows its "one" and "many" slots side by side: a slot whose key ends
 * `_one` shares a row with the next slot when that slot has the same key
 * ending `_many`. Every other slot has a row of its own.
 *
 * @param slots - The tab's slots in page order.
 * @returns The rows in page order, each one or two slots.
 */
export function copySlotRows(slots: CopySlot[]): CopySlot[][] {
  const rows: CopySlot[][] = [];
  for (let index = 0; index < slots.length; index += 1) {
    const slot = slots[index];
    const next = slots[index + 1];
    const { one, many } = countSlotEndings;
    const manyKey = slot.key.endsWith(one)
      ? `${slot.key.slice(0, -one.length)}${many}`
      : null;
    if (next && next.key === manyKey) {
      rows.push([slot, next]);
      index += 1;
    } else {
      rows.push([slot]);
    }
  }
  return rows;
}
