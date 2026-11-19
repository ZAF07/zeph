import { CopyLoadFailed } from "@/components/CopyLoadFailed";
import { PageHeader } from "@/components/PageHeader";
import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";
import { pickCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The Connect Telegram page: one tap opens Zeph in Telegram with a one-time
 * link. A phone has no QR code, so its line talks only about the button.
 * The card's words come from Copy, read on the server; only its slots go
 * to the browser.
 *
 * @returns The page, or the couldn't-load block when Copy can't be read.
 */
export default async function ConnectTelegramPage() {
  const copy = await loadCopy();
  return (
    <>
      <PageHeader
        eyebrow="Telegram Connection"
        title="Connect Telegram"
        lead={
          <>
            You talk to Zeph in Telegram.{" "}
            <span className="max-[899px]:hidden">
              Open the link on this device, or scan the code with your phone.
            </span>
            <span className="min-[900px]:hidden">
              Tap the button and Telegram opens with Zeph ready.
            </span>
          </>
        }
      />
      {copy ? (
        <TelegramConnectionCard
          copy={pickCopy(copy, ["connect_telegram.card."])}
        />
      ) : (
        <CopyLoadFailed />
      )}
    </>
  );
}
