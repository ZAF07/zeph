import Link from "next/link";

import { EmptyState } from "@/components/EmptyState";
import { HomeCard } from "@/components/HomeCard";
import { cardLink } from "@/components/text-link-styles";
import type { MemoryItem } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";

/**
 * "What you're working toward": the User's Goals Memory Items, read-only,
 * with the day each was remembered and a link to Memories.
 *
 * @param props - `goals` are the Goals Memory Items, newest first;
 *   `timeZone` is the User's.
 * @returns The card.
 */
export function HomeGoals({
  goals,
  timeZone,
}: {
  goals: MemoryItem[];
  timeZone?: string;
}) {
  return (
    <HomeCard
      headingId="home-goals-heading"
      title="What you're working toward"
      aside={
        <Link href="/memories" className={cardLink}>
          See in Memories
        </Link>
      }
      basis="wide"
    >
      {goals.length === 0 ? (
        <EmptyState
          title="Nothing here yet"
          body="When you mention something you’re working toward, Zeph will remember it here."
        />
      ) : (
        <ul className="m-0 list-none p-0">
          {goals.map((goal) => (
            <li
              key={goal.id}
              className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-t border-line py-3 first:border-t-0"
            >
              <span className="text-[15px] font-normal text-text">
                {goal.content}
              </span>
              <span className="text-[12px] text-soft">
                {`Remembered ${formatShortDay(goal.updated_at, timeZone)}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </HomeCard>
  );
}
