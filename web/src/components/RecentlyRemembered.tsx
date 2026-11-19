import Link from "next/link";

import { EmptyState } from "@/components/EmptyState";
import { HomeCard } from "@/components/HomeCard";
import { cardLink, cardListRow } from "@/components/card-styles";
import type { RememberedItem } from "@/lib/api-client";
import { readCopy, type Copy } from "@/lib/copy";

/**
 * "Recently remembered": the User's newest Memory Items with their Memory
 * Category, and a link to Memories.
 *
 * @param props - `copy` is Home's Copy; `items` are the newest Memory Items,
 *   newest first.
 * @returns The card.
 */
export function RecentlyRemembered({
  copy,
  items,
}: {
  copy: Copy;
  items: RememberedItem[];
}) {
  const text = (key: string) => readCopy(copy, `home.recent.${key}`);
  return (
    <HomeCard
      headingId="recently-remembered-heading"
      title={text("title")}
      aside={
        <Link href="/memories" className={cardLink}>
          {text("review_link")}
        </Link>
      }
      basis="wide"
    >
      {items.length === 0 ? (
        <EmptyState title={text("empty_title")} body={text("empty_body")} />
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
