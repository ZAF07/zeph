import Link from "next/link";

import { HomeCard } from "@/components/HomeCard";
import { cardLink } from "@/components/card-styles";
import type { TelegramConnection } from "@/lib/api-client";
import { fillPlaceholders, readCopy, type Copy } from "@/lib/copy";

/**
 * The Dashboard home card for a made Telegram Connection: who it is
 * connected as, and the way to manage it.
 *
 * @param props - `copy` is Home's Copy; `connection` is the Telegram
 *   Connection.
 * @returns The card.
 */
export function HomeTelegramCard({
  copy,
  connection,
}: {
  copy: Copy;
  connection: TelegramConnection;
}) {
  const text = (key: string) => readCopy(copy, `home.telegram.${key}`);
  return (
    <HomeCard
      headingId="home-telegram-heading"
      title={text("title")}
      caption={text("caption")}
      basis="narrow"
    >
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="size-[9px] rounded-full bg-cream" />
        <span className="min-w-0 text-[16px] font-normal text-text [overflow-wrap:anywhere]">
          {connection.telegram_username
            ? fillPlaceholders(text("connected_as"), {
                username: connection.telegram_username,
              })
            : text("connected_no_username")}
        </span>
      </div>
      <div className="mt-2">
        <Link href="/connect-telegram" className={cardLink}>
          {text("manage_link")}
        </Link>
      </div>
    </HomeCard>
  );
}
