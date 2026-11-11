import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelegramStatusCard } from "@/components/TelegramStatusCard";
import type { ApiClient } from "@/lib/api-client";

const apiClient = {
  getTelegramConnection: vi.fn<ApiClient["getTelegramConnection"]>(),
  createConnectionToken: vi.fn<ApiClient["createConnectionToken"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

describe("TelegramStatusCard", () => {
  beforeEach(() => {
    apiClient.getTelegramConnection.mockReset();
  });

  it("offers Connect Telegram when not connected", async () => {
    apiClient.getTelegramConnection.mockResolvedValue({
      connection: null,
      latest_token: null,
    });

    render(<TelegramStatusCard />);

    expect(
      await screen.findByRole("link", { name: "Connect Telegram" }),
    ).toHaveAttribute("href", "/connect-telegram");
  });

  it("shows who Telegram is connected as", async () => {
    apiClient.getTelegramConnection.mockResolvedValue({
      connection: {
        telegram_username: "maya_l",
        connected_at: "2026-11-11T09:02:00Z",
      },
      latest_token: null,
    });

    render(<TelegramStatusCard />);

    expect(
      await screen.findByText("Telegram connected as @maya_l."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Connect Telegram" }),
    ).not.toBeInTheDocument();
  });

  it("says so when the status could not be loaded", async () => {
    apiClient.getTelegramConnection.mockRejectedValue(new Error("down"));

    render(<TelegramStatusCard />);

    expect(
      await screen.findByText(
        "We couldn’t load this. Nothing you’ve shared is lost.",
      ),
    ).toBeInTheDocument();
  });
});
