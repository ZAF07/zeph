import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StickerLibrary } from "@/components/StickerLibrary";
import { ApiError, type ApiClient, type Sticker } from "@/lib/api-client";

const apiClient = {
  listStickers: vi.fn<ApiClient["listStickers"]>(),
  importStickerSet: vi.fn<ApiClient["importStickerSet"]>(),
  saveStickerNote: vi.fn<ApiClient["saveStickerNote"]>(),
  removeSticker: vi.fn<ApiClient["removeSticker"]>(),
  getStickerImage: vi.fn<ApiClient["getStickerImage"]>(),
  getTelegramConnection: vi.fn<ApiClient["getTelegramConnection"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function sticker(id: string, emoji: string, note: string): Sticker {
  return {
    id,
    emoji,
    set_name: "CalmCreatures",
    note,
    has_image: false,
    added_at: "2026-11-12T09:00:00Z",
  };
}

const seedling = sticker("seedling", "🌱", "Celebrating a small step forward");
const leaf = sticker("leaf", "🍃", "");

function cardFor(emoji: string): ReturnType<typeof within> {
  const card = screen.getByLabelText(`Emoji: ${emoji}`).closest("li");
  if (!card) {
    throw new Error(`No card for ${emoji}`);
  }
  return within(card);
}

describe("StickerLibrary", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listStickers.mockResolvedValue([seedling, leaf]);
    apiClient.getTelegramConnection.mockResolvedValue({
      connection: {
        telegram_username: "maya_l",
        connected_at: "2026-11-01T09:00:00Z",
      },
      latest_token: null,
    });
  });

  it("lists stickers with their notes and marks the ones that need a note", async () => {
    render(<StickerLibrary />);

    expect(await screen.findByText("2 stickers")).toBeInTheDocument();
    expect(
      cardFor("🌱").getByRole("textbox", { name: "When to use" }),
    ).toHaveValue("Celebrating a small step forward");
    expect(cardFor("🌱").queryByText("Needs a note")).toBeNull();
    expect(cardFor("🍃").getByText("Needs a note")).toBeInTheDocument();
  });

  it("shows the empty state when there are no stickers", async () => {
    apiClient.listStickers.mockResolvedValue([]);

    render(<StickerLibrary />);

    expect(await screen.findByText("No stickers yet")).toBeInTheDocument();
    expect(
      screen.getByText("Zeph replies in words only until you add some."),
    ).toBeInTheDocument();
  });

  it("shows an error with Try again when the stickers can't load", async () => {
    apiClient.listStickers.mockRejectedValueOnce(new Error("down"));

    render(<StickerLibrary />);

    const alert = await screen.findByRole("alert");
    expect(
      within(alert).getByText("Couldn’t load stickers"),
    ).toBeInTheDocument();
    await userEvent.click(
      within(alert).getByRole("button", { name: "Try again" }),
    );
    expect(await screen.findByText("2 stickers")).toBeInTheDocument();
  });

  it("imports a sticker set by name and shows how many were added", async () => {
    apiClient.importStickerSet.mockResolvedValue(2);
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    await userEvent.type(
      screen.getByRole("textbox", { name: "Sticker set name" }),
      "CalmCreatures",
    );
    await userEvent.click(screen.getByRole("button", { name: "Import set" }));

    expect(apiClient.importStickerSet).toHaveBeenCalledWith("CalmCreatures");
    expect(
      await screen.findByText(
        "Added 2 stickers from CalmCreatures. Add notes so Zeph can use them.",
      ),
    ).toBeInTheDocument();
    expect(apiClient.listStickers).toHaveBeenCalledTimes(2);
  });

  it("says why a sticker set couldn't be imported", async () => {
    apiClient.importStickerSet.mockRejectedValue(
      new ApiError(
        404,
        "/api/admin/stickers/import",
        "There is no sticker set called “Nope”.",
      ),
    );
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    await userEvent.type(
      screen.getByRole("textbox", { name: "Sticker set name" }),
      "Nope",
    );
    await userEvent.click(screen.getByRole("button", { name: "Import set" }));

    expect(
      await screen.findByText("There is no sticker set called “Nope”."),
    ).toBeInTheDocument();
  });

  it("tells Admins which Telegram account to send stickers from", async () => {
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    await userEvent.click(
      screen.getByRole("tab", { name: "Send from your Telegram" }),
    );

    expect(
      await screen.findByText("Listening for stickers from @maya_l…"),
    ).toBeInTheDocument();
  });

  it("asks Admins without Telegram to connect it first", async () => {
    apiClient.getTelegramConnection.mockResolvedValue({
      connection: null,
      latest_token: null,
    });
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    await userEvent.click(
      screen.getByRole("tab", { name: "Send from your Telegram" }),
    );

    expect(
      await screen.findByRole("link", { name: "Connect Telegram" }),
    ).toHaveAttribute("href", "/connect-telegram");
  });

  it("saves a changed note when leaving the field", async () => {
    apiClient.saveStickerNote.mockResolvedValue({
      ...leaf,
      note: "A calm moment",
    });
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    const note = cardFor("🍃").getByRole("textbox", { name: "When to use" });
    await userEvent.type(note, "A calm moment");
    await userEvent.tab();

    expect(apiClient.saveStickerNote).toHaveBeenCalledWith(
      "leaf",
      "A calm moment",
    );
    expect(await cardFor("🍃").findByText("Saved")).toBeInTheDocument();
    expect(cardFor("🍃").queryByText("Needs a note")).toBeNull();
  });

  it("does not save a note that was not changed", async () => {
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    await userEvent.click(
      cardFor("🌱").getByRole("textbox", { name: "When to use" }),
    );
    await userEvent.tab();

    expect(apiClient.saveStickerNote).not.toHaveBeenCalled();
  });

  it("shows when a note couldn't be saved", async () => {
    apiClient.saveStickerNote.mockRejectedValue(new Error("down"));
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");

    await userEvent.type(
      cardFor("🍃").getByRole("textbox", { name: "When to use" }),
      "Calm",
    );
    await userEvent.tab();

    expect(
      await cardFor("🍃").findByText("Couldn’t save. Try again."),
    ).toBeInTheDocument();
  });

  it("removes a sticker", async () => {
    apiClient.removeSticker.mockResolvedValue();
    render(<StickerLibrary />);
    await screen.findByText("2 stickers");
    apiClient.listStickers.mockResolvedValue([seedling]);

    await userEvent.click(
      cardFor("🍃").getByRole("button", { name: "Remove" }),
    );

    expect(apiClient.removeSticker).toHaveBeenCalledWith("leaf");
    expect(await screen.findByText("1 sticker")).toBeInTheDocument();
    expect(screen.queryByLabelText("Emoji: 🍃")).toBeNull();
  });

  it("shows a sticker's image when it has one", async () => {
    apiClient.listStickers.mockResolvedValue([
      { ...seedling, has_image: true },
    ]);
    apiClient.getStickerImage.mockResolvedValue(
      new Blob(["webp"], { type: "image/webp" }),
    );
    URL.createObjectURL = vi.fn(() => "blob:seedling");
    URL.revokeObjectURL = vi.fn();

    render(<StickerLibrary />);

    expect(await screen.findByAltText("Sticker: 🌱")).toHaveAttribute(
      "src",
      "blob:seedling",
    );
    expect(apiClient.getStickerImage).toHaveBeenCalledWith("seedling");
  });
});
