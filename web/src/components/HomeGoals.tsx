import Link from "next/link";

import type { MemoryItem } from "@/lib/api-client";
import { memorySourceLabel } from "@/lib/memories";

/**
 * "What you're working toward": the User's Goals Memory Items, read-only,
 * with a link to Memories.
 *
 * @param props - `goals` are the Goals Memory Items, newest first;
 *   `timeZone` is the User's.
 * @returns The section.
 */
export function HomeGoals({
  goals,
  timeZone,
}: {
  goals: MemoryItem[];
  timeZone?: string;
}) {
  return (
    <section
      aria-labelledby="home-goals-heading"
      className="flex flex-col gap-4"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h2 id="home-goals-heading" className="m-0 text-h2 font-normal">
          What you’re working toward
        </h2>
        <Link
          href="/memories"
          className="inline-flex min-h-11 items-center text-sm"
        >
          See in Memories
        </Link>
      </div>
      {goals.length === 0 ? (
        <div className="flex flex-col gap-1 rounded-card border border-dashed border-line-strong px-6 py-8 text-center">
          <span className="text-h3">Nothing here yet</span>
          <p className="m-0 text-caption text-ink-muted">
            When you mention something you’re working toward, Zeph will remember
            it here.
          </p>
        </div>
      ) : (
        <ul className="m-0 list-none rounded-card border border-line bg-white p-0">
          {goals.map((goal, index) => (
            <li
              key={goal.id}
              className={`flex flex-col px-6 py-4 ${index === 0 ? "" : "border-t border-line"}`}
            >
              <span className="font-medium">{goal.content}</span>
              <span className="text-caption text-ink-muted">
                {memorySourceLabel(goal, timeZone)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
