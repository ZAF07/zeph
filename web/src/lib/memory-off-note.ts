import type { Me } from "@/lib/api-client";
import { readCopy, type Copy } from "@/lib/copy";

/** The title and body of the note saying User Memory is off and why. */
export type MemoryOffNote = { title: string; body: string };

/**
 * Picks the Shared Copy note saying User Memory is off, and why. The
 * Admin's switch has the final say, so its "isn't available" note wins
 * over the User's own "paused" one.
 *
 * @param copy - Copy holding the `shared.memory_off.*` slots.
 * @param memory - The User's own User Memory switch and whether the Admin
 *   side allows User Memory for them.
 * @returns The note's title and body, or null while User Memory works.
 * @throws MissingCopyError if the Copy has no such slot.
 */
export function memoryOffNote(
  copy: Copy,
  memory: Pick<Me, "user_memory_enabled" | "user_memory_available">,
): MemoryOffNote | null {
  if (memory.user_memory_available && memory.user_memory_enabled) {
    return null;
  }
  const slot = memory.user_memory_available ? "paused" : "not_available";
  return {
    title: readCopy(copy, `shared.memory_off.${slot}_title`),
    body: readCopy(copy, `shared.memory_off.${slot}_body`),
  };
}
