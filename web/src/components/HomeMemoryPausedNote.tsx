/**
 * The note a Dashboard home memory section shows while User Memory is off,
 * instead of an empty list.
 *
 * @returns The note.
 */
export function HomeMemoryPausedNote() {
  return (
    <p className="m-0 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep">
      Memory is paused, so Zeph isn’t keeping or using memories. You can turn it
      back on in Memories.
    </p>
  );
}
