import Link from "next/link";

import { EmptyState } from "@/components/EmptyState";
import { HomeCard } from "@/components/HomeCard";
import { cardLink, cardListRow } from "@/components/card-styles";
import type { RememberedItem } from "@/lib/api-client";

/**
 * "Recently remembered": the User's newest Memory Items with their Memory
 * Category, and a link to Memories.
 *
 * @param props - `items` are the newest Memory Items, newest first.
 * @returns The card.
 */
export function RecentlyRemembered({ items }: { items: RememberedItem[] }) {
  return (
    <HomeCard
      headingId="recently-remembered-heading"
      title="Recently remembered"
      aside={
        <Link href="/memories" className={cardLink}>
          Review all
        </Link>
      }
      basis="wide"
    >
      {items.length === 0 ? (
        <EmptyState
          title="No memories yet"
          body="They’ll appear after your first Conversation."
        />
      ) : (
        <ul className="m-0 list-none p-0">
          {items.map((item) => (
            <li key={item.id} className={cardListRow}>
              <span className="text-[14px] text-text">{item.content}</span>
              <span className="text-[12px] text-soft">{item.category}</span>
            </li>
          ))}
        </ul>
      )}
    </HomeCard>
  );
}
