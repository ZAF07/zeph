import Link from "next/link";

import { HomeMemoryPausedNote } from "@/components/HomeMemoryPausedNote";
import type { RememberedItem } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";

/**
 * "Recently remembered": the User's newest Memory Items with their Memory
 * Category and date, and a link to Memories.
 *
 * @param props - `items` are the newest Memory Items, newest first;
 *   `memoryOn` says whether User Memory is on; `timeZone` is the User's.
 * @returns The section.
 */
export function RecentlyRemembered({
  items,
  memoryOn,
  timeZone,
}: {
  items: RememberedItem[];
  memoryOn: boolean;
  timeZone?: string;
}) {
  return (
    <section
      aria-labelledby="recently-remembered-heading"
      className="flex flex-col gap-1 rounded-card border border-line bg-white p-7"
    >
      <div className="flex items-baseline justify-between gap-4 pb-2">
        <h2
          id="recently-remembered-heading"
          className="m-0 text-h3 font-semibold"
        >
          Recently remembered
        </h2>
        <Link
          href="/memories"
          className="inline-flex min-h-11 items-center text-sm"
        >
          Review all
        </Link>
      </div>
      {!memoryOn ? (
        <HomeMemoryPausedNote />
      ) : items.length === 0 ? (
        <p className="m-0 border-t border-line pt-3.5 text-caption text-ink-muted">
          No memories yet. They’ll appear after your first Conversation.
        </p>
      ) : (
        <ul className="m-0 flex list-none flex-col p-0">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex flex-col border-t border-line py-3.5"
            >
              <span>{item.content}</span>
              <span className="text-caption text-ink-muted">
                {`${item.category} · ${formatShortDay(item.updated_at, timeZone)}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
