import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminFeatures } from "@/components/AdminFeatures";
import type { ApiClient, FeatureSwitch } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listFeatures: vi.fn<ApiClient["listFeatures"]>(),
  setFeatureForEveryone: vi.fn<ApiClient["setFeatureForEveryone"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const webSearch: FeatureSwitch = {
  feature: "web_search",
  name: "Web Search",
  description: "Zeph can look things up on the web.",
  on: true,
  changed_by_email: null,
  changed_at: null,
};

function rowFor(name: string): HTMLElement {
  const row = screen.getByText(name).closest("li");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return row;
}

describe("AdminFeatures", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listFeatures.mockResolvedValue([webSearch]);
  });

  it("lists each Feature with its description, switch and last change", async () => {
    renderWithQueries(<AdminFeatures />);

    await screen.findByText("Web Search");
    const row = within(rowFor("Web Search"));
    expect(row.getByText("Zeph can look things up on the web.")).toBeVisible();
    expect(
      row.getByRole("switch", { name: "Web Search for everyone" }),
    ).toHaveAttribute("aria-checked", "true");
    expect(row.getByText("Never changed")).toBeVisible();
  });

  it("shows who changed a switch last and when", async () => {
    apiClient.listFeatures.mockResolvedValue([
      {
        ...webSearch,
        on: false,
        changed_by_email: "maya@example.com",
        changed_at: "2026-11-13T09:00:00Z",
      },
    ]);
    renderWithQueries(<AdminFeatures />);

    await screen.findByText("Web Search");
    const row = within(rowFor("Web Search"));
    expect(row.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    expect(row.getByText(/13 Nov, .* by maya@example\.com/)).toBeVisible();
  });

  it("turns a Feature off for everyone and shows the new last change", async () => {
    apiClient.setFeatureForEveryone.mockResolvedValue({
      ...webSearch,
      on: false,
      changed_by_email: "owner@example.com",
      changed_at: "2026-11-13T10:00:00Z",
    });
    const user = userEvent.setup();
    renderWithQueries(<AdminFeatures />);

    await user.click(
      await screen.findByRole("switch", { name: "Web Search for everyone" }),
    );

    expect(apiClient.setFeatureForEveryone).toHaveBeenCalledWith(
      "web_search",
      false,
    );
    const row = within(rowFor("Web Search"));
    expect(row.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    expect(
      await row.findByText(/13 Nov, .* by owner@example\.com/),
    ).toBeVisible();
  });

  it("keeps the switch as it was when the change fails", async () => {
    apiClient.setFeatureForEveryone.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<AdminFeatures />);

    await user.click(
      await screen.findByRole("switch", { name: "Web Search for everyone" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t change Web Search. It is still on.",
    );
    expect(
      screen.getByRole("switch", { name: "Web Search for everyone" }),
    ).toHaveAttribute("aria-checked", "true");
  });

  it("lists Stickers and Knowledge with their switches and turns them back on", async () => {
    apiClient.listFeatures.mockResolvedValue([
      webSearch,
      {
        feature: "stickers",
        name: "Stickers",
        description: "Zeph can add a sticker to a reply.",
        on: false,
        changed_by_email: "maya@example.com",
        changed_at: "2026-11-13T09:00:00Z",
      },
      {
        feature: "knowledge",
        name: "Knowledge",
        description: "Zeph gets passages that may fit the message.",
        on: true,
        changed_by_email: null,
        changed_at: null,
      },
    ]);
    apiClient.setFeatureForEveryone.mockResolvedValue({
      feature: "stickers",
      name: "Stickers",
      description: "Zeph can add a sticker to a reply.",
      on: true,
      changed_by_email: "owner@example.com",
      changed_at: "2026-11-13T10:00:00Z",
    });
    const user = userEvent.setup();
    renderWithQueries(<AdminFeatures />);

    await screen.findByText("Stickers");
    const stickers = within(rowFor("Stickers"));
    const knowledge = within(rowFor("Knowledge"));
    expect(
      stickers.getByText("Zeph can add a sticker to a reply."),
    ).toBeVisible();
    expect(stickers.getByText(/13 Nov, .* by maya@example\.com/)).toBeVisible();
    expect(
      knowledge.getByText("Zeph gets passages that may fit the message."),
    ).toBeVisible();
    expect(
      knowledge.getByRole("switch", { name: "Knowledge for everyone" }),
    ).toHaveAttribute("aria-checked", "true");
    expect(knowledge.getByText("Never changed")).toBeVisible();

    await user.click(
      stickers.getByRole("switch", { name: "Stickers for everyone" }),
    );

    expect(apiClient.setFeatureForEveryone).toHaveBeenCalledWith(
      "stickers",
      true,
    );
    expect(stickers.getByRole("switch")).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(
      await stickers.findByText(/13 Nov, .* by owner@example\.com/),
    ).toBeVisible();
  });

  it("lists Settings in Chat with its switch and turns it off", async () => {
    const settingsInChat: FeatureSwitch = {
      feature: "settings_in_chat",
      name: "Settings in Chat",
      description: "A User can change their settings by asking Zeph in chat.",
      on: true,
      changed_by_email: null,
      changed_at: null,
    };
    apiClient.listFeatures.mockResolvedValue([webSearch, settingsInChat]);
    apiClient.setFeatureForEveryone.mockResolvedValue({
      ...settingsInChat,
      on: false,
      changed_by_email: "owner@example.com",
      changed_at: "2026-11-13T10:00:00Z",
    });
    const user = userEvent.setup();
    renderWithQueries(<AdminFeatures />);

    await screen.findByText("Settings in Chat");
    const settings = within(rowFor("Settings in Chat"));
    expect(
      settings.getByText(
        "A User can change their settings by asking Zeph in chat.",
      ),
    ).toBeVisible();
    expect(settings.getByText("Never changed")).toBeVisible();

    await user.click(
      settings.getByRole("switch", { name: "Settings in Chat for everyone" }),
    );

    expect(apiClient.setFeatureForEveryone).toHaveBeenCalledWith(
      "settings_in_chat",
      false,
    );
    expect(settings.getByRole("switch")).toHaveAttribute(
      "aria-checked",
      "false",
    );
    expect(
      await settings.findByText(/13 Nov, .* by owner@example\.com/),
    ).toBeVisible();
  });

  it("offers Try again when the Features can't be loaded", async () => {
    apiClient.listFeatures.mockRejectedValueOnce(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<AdminFeatures />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Web Search")).toBeVisible();
  });
});
