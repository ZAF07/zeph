import Link from "next/link";

import { EmptyState } from "@/components/EmptyState";
import { HomeCard } from "@/components/HomeCard";
import { cardLink, cardListRow } from "@/components/card-styles";
import type { MemoryItem } from "@/lib/api-client";
import { fillCopy, readCopy, type Copy } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";

/**
 * "What you're working toward": the User's Goals Memory Items, read-only,
 * with the day each was remembered and a link to Memories.
 *
 * @param props - `copy` is Home's Copy; `goals` are the Goals Memory Items,
 *   newest first; `timeZone` is the User's.
 * @returns The card.
 */
export function HomeGoals({
  copy,
  goals,
  timeZone,
}: {
  copy: Copy;
  goals: MemoryItem[];
  timeZone?: string;
}) {
  const text = (key: string) => readCopy(copy, `home.goals.${key}`);
  return (
    <HomeCard
      headingId="home-goals-heading"
      title={text("title")}
      aside={
        <Link href="/memories" className={cardLink}>
          {text("memories_link")}
        </Link>
      }
      basis="wide"
    >
      {goals.length === 0 ? (
        <EmptyState title={text("empty_title")} body={text("empty_body")} />
      ) : (
        <ul className="m-0 list-none p-0">
          {goals.map((goal) => (
            <li key={goal.id} className={cardListRow}>
              <span className="text-[15px] font-normal text-text">
                {goal.content}
              </span>
              <span className="text-[12px] text-soft">
                {fillCopy(copy, "home.goals.remembered", {
                  day: formatShortDay(goal.updated_at, timeZone),
                })}
              </span>
            </li>
          ))}
        </ul>
      )}
    </HomeCard>
  );
}
