import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PersonalStickersSection } from "@/components/PersonalStickersSection";
import type { ApiClient, PersonalSticker } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listPersonalStickers: vi.fn<ApiClient["listPersonalStickers"]>(),
  getPersonalStickerImage: vi.fn<ApiClient["getPersonalStickerImage"]>(),
  deletePersonalSticker: vi.fn<ApiClient["deletePersonalSticker"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const laugh: PersonalSticker = {
  id: "laugh",
  emoji: "😂",
  note: "For laughing along at a small mishap.",
  has_image: true,
  kept_at: "2026-11-12T09:00:00Z",
};

const hug: PersonalSticker = {
  id: "hug",
  emoji: "🤗",
  note: "For sending warmth when a day went well.",
  has_image: false,
  kept_at: "2026-11-11T09:00:00Z",
};

describe("PersonalStickersSection", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    URL.createObjectURL = vi.fn(() => "blob:laugh");
    URL.revokeObjectURL = vi.fn();
    apiClient.listPersonalStickers.mockResolvedValue([laugh, hug]);
    apiClient.getPersonalStickerImage.mockResolvedValue(new Blob(["webp"]));
    apiClient.deletePersonalSticker.mockResolvedValue(undefined);
  });

  it("shows each kept sticker with its image and when Zeph uses it", async () => {
    renderWithQueries(<PersonalStickersSection available />);

    const section = await screen.findByRole("region", {
      name: "Your stickers",
    });
    expect(await within(section).findByAltText("Sticker: 😂")).toHaveAttribute(
      "src",
      "blob:laugh",
    );
    expect(within(section).getByText(laugh.note)).toBeVisible();
    expect(
      within(section).getByRole("img", { name: "Sticker: 🤗" }),
    ).toHaveTextContent("🤗");
    expect(within(section).getByText(hug.note)).toBeVisible();
    expect(apiClient.getPersonalStickerImage).toHaveBeenCalledWith("laugh");
    expect(apiClient.getPersonalStickerImage).not.toHaveBeenCalledWith("hug");
    expect(
      within(section).queryByText("Not available on your account"),
    ).toBeNull();
  });

  it("removes a sticker", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PersonalStickersSection available />);

    await user.click(
      await screen.findByRole("button", { name: "Remove sticker 🤗" }),
    );

    expect(apiClient.deletePersonalSticker).toHaveBeenCalledWith("hug");
    expect(screen.queryByText(hug.note)).toBeNull();
    expect(screen.getByText(laugh.note)).toBeVisible();
  });

  it("says when a sticker couldn't be removed and keeps it", async () => {
    apiClient.deletePersonalSticker.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<PersonalStickersSection available />);

    await user.click(
      await screen.findByRole("button", { name: "Remove sticker 🤗" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t remove that. Please try again.",
    );
    expect(screen.getByText(hug.note)).toBeVisible();
  });

  it("still shows kept stickers when the Feature isn't available", async () => {
    renderWithQueries(<PersonalStickersSection available={false} />);

    expect(
      await screen.findByText("Not available on your account"),
    ).toBeVisible();
    expect(await screen.findByText(laugh.note)).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Remove sticker 😂" }),
    ).toBeEnabled();
  });

  it("says when no sticker is kept yet", async () => {
    apiClient.listPersonalStickers.mockResolvedValue([]);
    renderWithQueries(<PersonalStickersSection available />);

    expect(await screen.findByText("No stickers kept yet")).toBeVisible();
  });

  it("offers Try again when the stickers can't load", async () => {
    apiClient.listPersonalStickers
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValueOnce([laugh]);
    const user = userEvent.setup();
    renderWithQueries(<PersonalStickersSection available />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText(laugh.note)).toBeVisible();
  });
});
