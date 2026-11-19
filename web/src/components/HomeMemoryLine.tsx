import { readCopy, type Copy } from "@/lib/copy";
import type { MemoryOffNote } from "@/lib/memory-off-note";

/**
 * The line on the Dashboard home about User Memory. While it is on, it says
 * so; while it is off, it says why, with the title in the brighter colour.
 *
 * @param props - `copy` is Home's Copy; `memoryOffNote` is the note saying
 *   User Memory is off, or null while it is on.
 * @returns The line.
 */
export function HomeMemoryLine({
  copy,
  memoryOffNote,
}: {
  copy: Copy;
  memoryOffNote: MemoryOffNote | null;
}) {
  const title = memoryOffNote?.title ?? readCopy(copy, "home.memory.on_title");
  const body = memoryOffNote?.body ?? readCopy(copy, "home.memory.on_body");
  return (
    <p
      role={memoryOffNote ? "status" : undefined}
      className="m-0 rounded-note border border-line px-5 py-3.5 text-[14px] text-soft"
    >
      <span className="text-text">{title}</span> {body}
    </p>
  );
}
