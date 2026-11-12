import Link from "next/link";

import type { TelegramConnection } from "@/lib/api-client";
import { lastConversationText } from "@/lib/home";

/**
 * The Dashboard home card for a made Telegram Connection: who it is
 * connected as and when the last Conversation was.
 *
 * @param props - `connection` is the Telegram Connection;
 *   `lastConversationAt` is when the last Conversation's newest message was
 *   sent, or null; `now` is the current moment; `timeZone` is the User's.
 * @returns The card.
 */
export function HomeTelegramCard({
  connection,
  lastConversationAt,
  now,
  timeZone,
}: {
  connection: TelegramConnection;
  lastConversationAt: string | null;
  now: Date;
  timeZone?: string;
}) {
  return (
    <section
      aria-labelledby="home-telegram-heading"
      className="flex flex-col gap-3 rounded-card border border-line bg-white p-7"
    >
      <h2
        id="home-telegram-heading"
        className="m-0 font-mono text-eyebrow font-semibold uppercase text-ink-muted"
      >
        Telegram
      </h2>
      <p className="m-0 flex items-center gap-2.5 text-[17px] font-medium">
        <span aria-hidden="true" className="size-2.5 rounded-full bg-blue" />
        {connection.telegram_username
          ? `Connected as @${connection.telegram_username}`
          : "Connected"}
      </p>
      <p className="m-0 text-[15px] text-ink-soft">
        {lastConversationText(lastConversationAt, now, timeZone)}
      </p>
      <Link
        href="/connect-telegram"
        className="inline-flex min-h-11 items-center self-start text-sm"
      >
        Manage connection
      </Link>
    </section>
  );
}
