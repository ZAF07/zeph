import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();
const cardCopy = vi.fn<(copy: Copy) => void>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/TelegramConnectionCard", () => ({
  TelegramConnectionCard: ({ copy }: { copy: Copy }) => {
    cardCopy(copy);
    return <p>{copy["connect_telegram.card.open_button"]}</p>;
  },
}));

const { default: ConnectTelegramPage, generateMetadata } =
  await import("@/app/(dashboard)/(user)/connect-telegram/page");

describe("the /connect-telegram page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
    cardCopy.mockReset();
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("gives the link card only its own Copy slots", async () => {
    render(await ConnectTelegramPage());

    expect(screen.getByText("Open in Telegram")).toBeInTheDocument();
    const keys = Object.keys(cardCopy.mock.lastCall?.[0] ?? {});
    expect(keys.length).toBeGreaterThan(0);
    expect(keys.every((key) => key.startsWith("connect_telegram.card."))).toBe(
      true,
    );
  });

  it("shows the couldn't-load block in place of the card when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await ConnectTelegramPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(cardCopy).not.toHaveBeenCalled();
  });

  it("words its heading and lead from an Admin's Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "connect_telegram.heading": "Link Telegram",
      "connect_telegram.lead": "Zeph lives in Telegram.",
    });

    render(await ConnectTelegramPage());

    expect(
      screen.getByRole("heading", { level: 1, name: "Link Telegram" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Zeph lives in Telegram\./)).toHaveTextContent(
      "Zeph lives in Telegram. Open the link on this device, or scan the code with your phone.Tap the button and Telegram opens with Zeph ready.",
    );
  });

  it("shows only Copy text", async () => {
    loadCopy.mockResolvedValue(markedCopy());

    const { container } = render(await ConnectTelegramPage());

    expect(wordsNotFromCopy(container)).toEqual([]);
  });

  it("takes its tab title and search description from Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "connect_telegram.page_title": "Zeph — Link Telegram",
      "connect_telegram.page_description": "Link your Telegram.",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph — Link Telegram",
      description: "Link your Telegram.",
    });
  });

  it("keeps the layout's title when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    expect(await generateMetadata()).toEqual({});
  });
});
