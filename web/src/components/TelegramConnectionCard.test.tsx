import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";
import type {
  ApiClient,
  ConnectionToken,
  TelegramConnectionStatus,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getTelegramConnection: vi.fn<ApiClient["getTelegramConnection"]>(),
  createConnectionToken: vi.fn<ApiClient["createConnectionToken"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function connectionToken(
  overrides: Partial<ConnectionToken> = {},
): ConnectionToken {
  return {
    token: "7Q2K-ZEPH",
    deep_link_url: "https://t.me/zeph_bot?start=7Q2K-ZEPH",
    bot_username: "zeph_bot",
    expires_at: "2026-11-11T09:15:00Z",
    status: "active",
    ...overrides,
  };
}

function notConnected(
  token: ConnectionToken | null = connectionToken(),
): TelegramConnectionStatus {
  return { connection: null, latest_token: token };
}

const connected: TelegramConnectionStatus = {
  connection: {
    telegram_username: "maya_l",
    connected_at: "2026-11-11T09:02:00Z",
  },
  latest_token: connectionToken({ status: "used" }),
};

describe("TelegramConnectionCard", () => {
  beforeEach(() => {
    apiClient.getTelegramConnection.mockReset();
    apiClient.createConnectionToken.mockReset();
  });

  it("shows the link ready: QR code, /start code and Open in Telegram", async () => {
    apiClient.getTelegramConnection.mockResolvedValue(notConnected());

    renderWithQueries(<TelegramConnectionCard />);

    const openLink = await screen.findByRole("link", {
      name: "Open in Telegram",
    });
    expect(openLink).toHaveAttribute(
      "href",
      "https://t.me/zeph_bot?start=7Q2K-ZEPH",
    );
    expect(
      screen.getByRole("img", { name: "QR code that opens Zeph in Telegram" }),
    ).toHaveClass("max-[899px]:hidden");
    expect(screen.getByText("/start 7Q2K-ZEPH")).toBeInTheDocument();
    expect(screen.getByText("@zeph_bot")).toBeInTheDocument();
  });

  it("shows the shared loading panel while the link loads", () => {
    apiClient.getTelegramConnection.mockReturnValue(new Promise(() => {}));

    renderWithQueries(<TelegramConnectionCard />);

    expect(
      screen.getByRole("status", { name: "Loading your Telegram link" }),
    ).toBeInTheDocument();
  });

  it("draws waiting as the main card with I’ve pressed Start as the cream pill", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValue(notConnected());

    renderWithQueries(<TelegramConnectionCard />);
    await user.click(
      await screen.findByRole("link", { name: "Open in Telegram" }),
    );

    const card = screen.getByRole("status");
    expect(card).toHaveClass("rounded-card", "bg-panel", "px-7", "py-[26px]");
    expect(
      within(card).getByText("Waiting for you to say hello in Telegram…"),
    ).toHaveClass("text-cream");
    expect(
      within(card).getByText(
        "Once you press Start in Telegram, this page will update on its own.",
      ),
    ).toBeInTheDocument();
    expect(
      within(card).getByRole("button", { name: "I’ve pressed Start" }),
    ).toHaveClass("bg-cream");
    expect(
      within(card).getByRole("button", { name: "Show the code again" }),
    ).toHaveClass("border-soft", "bg-transparent");
  });

  it("draws connected with the username and Go to your Dashboard", async () => {
    apiClient.getTelegramConnection.mockResolvedValue(connected);

    renderWithQueries(<TelegramConnectionCard />);

    const title = await screen.findByText("Zeph just said hello in Telegram");
    expect(title).toHaveClass("text-cream");
    expect(
      screen.getByText(
        "Connected as @maya_l. Reply whenever you’re ready, there’s no rush.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Go to your Dashboard" }),
    ).toHaveAttribute("href", "/");
  });

  it("draws expired with a coral title and Get a new link", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValueOnce(notConnected());

    renderWithQueries(<TelegramConnectionCard />);
    await screen.findByText("/start 7Q2K-ZEPH");
    apiClient.getTelegramConnection.mockResolvedValue(
      notConnected(connectionToken({ status: "expired" })),
    );
    await user.click(screen.getByRole("link", { name: "Open in Telegram" }));
    await user.click(
      screen.getByRole("button", { name: "I’ve pressed Start" }),
    );

    const card = await screen.findByRole("alert");
    expect(
      within(card).getByText("This link has expired or was already used"),
    ).toHaveClass("text-danger");
    expect(
      within(card).getByText(
        "For your security each link works once and only for a short while.",
      ),
    ).toBeInTheDocument();
    expect(
      within(card).getByRole("button", { name: "Get a new link" }),
    ).toHaveClass("bg-cream");
  });

  it("shows the compact ready link: QR code, Open in Telegram and expiry, no /start code", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValue(
      notConnected(
        connectionToken({
          expires_at: new Date(Date.now() + 14 * 60000).toISOString(),
        }),
      ),
    );

    renderWithQueries(<TelegramConnectionCard compact />);

    const openLink = await screen.findByRole("link", {
      name: "Open in Telegram",
    });
    expect(openLink).toHaveAttribute(
      "href",
      "https://t.me/zeph_bot?start=7Q2K-ZEPH",
    );
    expect(
      screen.getByRole("img", { name: "QR code that opens Zeph in Telegram" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Works once · expires in 14 minutes"),
    ).toBeInTheDocument();
    expect(screen.queryByText("/start 7Q2K-ZEPH")).not.toBeInTheDocument();

    await user.click(openLink);
    expect(
      screen.getByText("Waiting for you to say hello in Telegram…"),
    ).toBeInTheDocument();
  });

  it("creates a new link when there is no active one", async () => {
    apiClient.getTelegramConnection.mockResolvedValue(
      notConnected(connectionToken({ status: "expired" })),
    );
    apiClient.createConnectionToken.mockResolvedValue(
      connectionToken({ token: "NEW1-CODE" }),
    );

    renderWithQueries(<TelegramConnectionCard />);

    expect(await screen.findByText("/start NEW1-CODE")).toBeInTheDocument();
  });

  it("waits for hello after opening Telegram, then shows connected", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValueOnce(notConnected());

    renderWithQueries(<TelegramConnectionCard />);
    await user.click(
      await screen.findByRole("link", { name: "Open in Telegram" }),
    );

    expect(
      screen.getByText("Waiting for you to say hello in Telegram…"),
    ).toBeInTheDocument();

    apiClient.getTelegramConnection.mockResolvedValue(connected);
    await user.click(
      screen.getByRole("button", { name: "I’ve pressed Start" }),
    );

    expect(
      await screen.findByText("Zeph just said hello in Telegram"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Connected as @maya_l/)).toBeInTheDocument();
  });

  it("shows the code again from the waiting state", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValue(notConnected());

    renderWithQueries(<TelegramConnectionCard />);
    await user.click(
      await screen.findByRole("link", { name: "Open in Telegram" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Show the code again" }),
    );

    expect(screen.getByText("/start 7Q2K-ZEPH")).toBeInTheDocument();
  });

  it("shows expired, and Get a new link shows a fresh code", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValueOnce(notConnected());

    renderWithQueries(<TelegramConnectionCard />);
    await screen.findByText("/start 7Q2K-ZEPH");

    apiClient.getTelegramConnection.mockResolvedValue(
      notConnected(connectionToken({ status: "expired" })),
    );
    await user.click(screen.getByRole("link", { name: "Open in Telegram" }));
    await user.click(
      screen.getByRole("button", { name: "I’ve pressed Start" }),
    );

    expect(
      await screen.findByText("This link has expired or was already used"),
    ).toBeInTheDocument();

    apiClient.createConnectionToken.mockResolvedValue(
      connectionToken({ token: "NEW1-CODE" }),
    );
    await user.click(screen.getByRole("button", { name: "Get a new link" }));

    expect(await screen.findByText("/start NEW1-CODE")).toBeInTheDocument();
  });

  it("explains when the Telegram account is linked to another account", async () => {
    apiClient.getTelegramConnection.mockResolvedValue(
      notConnected(connectionToken({ status: "connected_elsewhere" })),
    );

    renderWithQueries(<TelegramConnectionCard />);

    expect(
      await screen.findByText(
        "That Telegram account is linked to another Zeph account",
      ),
    ).toHaveClass("text-danger");
    expect(
      screen.getByRole("button", { name: "Get a new link" }),
    ).toBeInTheDocument();
  });

  it("offers Try again when a link could not be created", async () => {
    const user = userEvent.setup();
    apiClient.getTelegramConnection.mockResolvedValue(notConnected(null));
    apiClient.createConnectionToken.mockRejectedValueOnce(new Error("down"));

    renderWithQueries(<TelegramConnectionCard />);

    expect(
      await screen.findByRole("heading", {
        name: "We couldn’t create your link",
      }),
    ).toHaveClass("text-danger");

    apiClient.createConnectionToken.mockResolvedValue(connectionToken());
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("/start 7Q2K-ZEPH")).toBeInTheDocument();
  });

  it("shows connected straight away when Telegram is already connected", async () => {
    apiClient.getTelegramConnection.mockResolvedValue(connected);

    renderWithQueries(<TelegramConnectionCard />);

    expect(await screen.findByText(/Connected as @maya_l/)).toBeInTheDocument();
    expect(apiClient.createConnectionToken).not.toHaveBeenCalled();
  });
});
