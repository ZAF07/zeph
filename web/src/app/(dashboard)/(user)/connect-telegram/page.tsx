import { PageHeader } from "@/components/PageHeader";
import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";

/**
 * The Connect Telegram page: one tap opens Zeph in Telegram with a one-time
 * link. A phone has no QR code, so its line talks only about the button.
 *
 * @returns The page.
 */
export default function ConnectTelegramPage() {
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
      <TelegramConnectionCard />
    </>
  );
}
