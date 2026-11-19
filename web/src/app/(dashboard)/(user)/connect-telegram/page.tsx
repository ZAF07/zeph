import type { Metadata } from "next";

import { CopyLoadFailed } from "@/components/CopyLoadFailed";
import { PageHeader } from "@/components/PageHeader";
import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";
import { pageMetadata, pickCopy, readCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The browser tab title and search description of Connect Telegram, from
 * Copy. When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  return copy ? pageMetadata(copy, "connect_telegram") : {};
}

/**
 * The Connect Telegram page: one tap opens Zeph in Telegram with a one-time
 * link. A phone has no QR code, so its line talks only about the button.
 * Every word comes from Copy, read on the server; only the card's slots go
 * to the browser.
 *
 * @returns The page, or the couldn't-load block when Copy can't be read.
 */
export default async function ConnectTelegramPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <CopyLoadFailed />;
  }
  const text = (key: string) => readCopy(copy, `connect_telegram.${key}`);
  return (
    <>
      <PageHeader
        eyebrow={text("eyebrow")}
        title={text("heading")}
        lead={
          <>
            {text("lead")}{" "}
            <span className="max-[899px]:hidden">{text("lead_computer")}</span>
            <span className="min-[900px]:hidden">{text("lead_phone")}</span>
          </>
        }
      />
      <TelegramConnectionCard
        copy={pickCopy(copy, ["connect_telegram.card."])}
      />
    </>
  );
}
