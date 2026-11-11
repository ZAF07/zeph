import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";

/**
 * The Connect Telegram page: one tap opens Zeph in Telegram with a one-time
 * link.
 *
 * @returns The page.
 */
export default function ConnectTelegramPage() {
  return (
    <>
      <header className="flex max-w-[720px] flex-col gap-2">
        <p className="m-0 font-mono text-eyebrow font-semibold uppercase text-orange-text">
          Telegram Connection
        </p>
        <h1 className="m-0 text-h1 font-normal">Connect Telegram</h1>
        <p className="m-0 text-lead text-ink-soft">
          You talk to Zeph in Telegram. Open the link on this device, or scan
          the code with your phone.
        </p>
      </header>
      <TelegramConnectionCard />
    </>
  );
}
