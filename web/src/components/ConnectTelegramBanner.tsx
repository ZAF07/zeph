import Link from "next/link";

/**
 * The strong dark card on the Dashboard home when Telegram isn't connected,
 * since Zeph can only reach the User there.
 *
 * @returns The card, leading to Connect Telegram.
 */
export function ConnectTelegramBanner() {
  return (
    <section
      aria-labelledby="connect-telegram-heading"
      className="flex flex-wrap items-center justify-between gap-6 rounded-2xl bg-black p-8 text-subtle"
    >
      <div className="flex min-w-0 flex-[1_1_360px] flex-col gap-2">
        <h2
          id="connect-telegram-heading"
          className="m-0 text-[32px] font-normal leading-[1.15]"
        >
          Zeph can’t reach you yet.
        </h2>
        <p className="m-0 text-[15px] text-on-black-soft">
          Conversations and Check-ins happen in Telegram. Connect once and Zeph
          will say hello.
        </p>
      </div>
      <Link
        href="/connect-telegram"
        className="inline-flex min-h-[52px] items-center justify-center whitespace-nowrap rounded-full border border-white bg-white px-6 py-3 text-[15px] font-medium text-ink no-underline hover:text-ink"
      >
        Connect Telegram
      </Link>
    </section>
  );
}
