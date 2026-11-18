import Link from "next/link";

import { HomeCard } from "@/components/HomeCard";
import { cardLink } from "@/components/card-styles";
import type { TelegramConnection } from "@/lib/api-client";

/**
 * The Dashboard home card for a made Telegram Connection: who it is
 * connected as, and the way to manage it.
 *
 * @param props - `connection` is the Telegram Connection.
 * @returns The card.
 */
export function HomeTelegramCard({
  connection,
}: {
  connection: TelegramConnection;
}) {
  return (
    <HomeCard
      headingId="home-telegram-heading"
      title="Telegram"
      caption="Where your conversations with Zeph happen."
      basis="narrow"
    >
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="size-[9px] rounded-full bg-cream" />
        <span className="min-w-0 text-[16px] font-normal text-text [overflow-wrap:anywhere]">
          {connection.telegram_username
            ? `Connected as @${connection.telegram_username}`
            : "Connected"}
        </span>
      </div>
      <div className="mt-2">
        <Link href="/connect-telegram" className={cardLink}>
          Manage connection
        </Link>
      </div>
    </HomeCard>
  );
}
