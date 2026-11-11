import { TelegramStatusCard } from "@/components/TelegramStatusCard";

/**
 * The Dashboard home page. For now it shows the Telegram Connection status;
 * the full home page arrives in a later issue.
 *
 * @returns The page.
 */
export default function HomePage() {
  return (
    <>
      <header className="flex flex-col gap-2">
        <p className="m-0 font-mono text-eyebrow font-semibold uppercase text-orange-text">
          Home
        </p>
        <h1 className="m-0 text-h1 font-normal">Welcome to Zeph</h1>
      </header>
      <TelegramStatusCard />
    </>
  );
}
