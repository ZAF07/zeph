import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountSettings } from "@/components/AccountSettings";
import {
  ApiError,
  type ApiClient,
  type Me,
  type PlatformContent,
} from "@/lib/api-client";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
  deleteMyData: vi.fn<ApiClient["deleteMyData"]>(),
  deleteAccount: vi.fn<ApiClient["deleteAccount"]>(),
  listPersonalStickers: vi.fn<ApiClient["listPersonalStickers"]>(),
};

const signOut = vi.fn<(redirectUrl: string) => Promise<void>>();

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

vi.mock("@/lib/auth/client", () => ({
  useSignOut: () => signOut,
}));

const content: PlatformContent = {
  onboarding_reason_choices: [],
  message_retention_days: 14,
};

const editedCopy = {
  ...seedCopy(),
  "shared.memory_explanation": "Edited memory explanation.",
  "account.photos.explanation":
    "When off, Zeph won’t look at or remember your photos. Every photo is still checked for safety.\n\nWhen on, Zeph looks at your photos.",
  "account.delete_data.description":
    "Removes your messages, memories and the private notes Zeph keeps.",
};

const onboardedUser: Me = {
  id: "user-1",
  email: "maya@example.com",
  name: "Maya",
  onboarding_reasons: ["Relationships"],
  onboarding_note: null,
  country: "SG",
  time_zone: "Asia/Singapore",
  ai_notice_acknowledged_at: "2026-11-11T09:00:00Z",
  user_memory_enabled: true,
  user_memory_available: true,
  photo_viewing_enabled: true,
  photo_viewing_available: true,
  personal_stickers_available: true,
  pattern_noticing_notice: false,
  onboarding_completed_at: "2026-11-11T09:00:00Z",
  role: "user",
  changed_in_chat: {},
};

describe("AccountSettings", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getMe.mockResolvedValue(onboardedUser);
    apiClient.getPlatformContent.mockResolvedValue(content);
    apiClient.updatePreferences.mockImplementation(async (changes) => ({
      ...onboardedUser,
      ...changes,
    }));
    apiClient.deleteMyData.mockResolvedValue(undefined);
    apiClient.deleteAccount.mockResolvedValue(undefined);
    apiClient.listPersonalStickers.mockResolvedValue([]);
    signOut.mockResolvedValue(undefined);
  });

  it("shows the Your stickers section, saying when it isn't available", async () => {
    apiClient.getMe.mockResolvedValue({
      ...onboardedUser,
      personal_stickers_available: false,
    });
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    const section = await screen.findByRole("region", {
      name: "Your stickers",
    });
    expect(
      within(section).getByText("Not available on your account"),
    ).toBeVisible();
  });

  it("says what Delete my data removes, private notes included", async () => {
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    const yourData = within(
      await screen.findByRole("region", { name: "Delete my data" }),
    );
    expect(
      yourData.getByText(
        "Removes your messages, memories and the private notes Zeph keeps.",
      ),
    ).toBeVisible();
  });

  it("marks the time zone and User Memory as changed in chat", async () => {
    apiClient.getMe.mockResolvedValue({
      ...onboardedUser,
      changed_in_chat: {
        time_zone: "2026-11-03T09:00:00Z",
        user_memory: "2026-11-05T09:00:00Z",
      },
    });
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    expect(
      await screen.findByText("Changed in chat · 3 Nov"),
    ).toBeInTheDocument();
    expect(screen.getByText("Changed in chat · 5 Nov")).toBeInTheDocument();
  });

  it("drops the time zone caption once the profile is saved", async () => {
    apiClient.getMe.mockResolvedValue({
      ...onboardedUser,
      changed_in_chat: { time_zone: "2026-11-03T09:00:00Z" },
    });
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    await screen.findByText("Changed in chat · 3 Nov");

    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    expect(screen.queryByText(/Changed in chat/)).not.toBeInTheDocument();
  });

  it("shows the saved profile", async () => {
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    expect(await screen.findByLabelText("What Zeph calls you")).toHaveValue(
      "Maya",
    );
    expect(screen.getByText("maya@example.com")).toBeInTheDocument();
    expect(screen.getByLabelText("Country")).toHaveValue("SG");
    expect(screen.getByLabelText("Time zone")).toHaveValue("Asia/Singapore");
  });

  it("saves a changed name, country and time zone", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const nameField = await screen.findByLabelText("What Zeph calls you");

    await user.clear(nameField);
    await user.type(nameField, "May");
    await user.selectOptions(screen.getByLabelText("Country"), ["GB"]);
    await user.selectOptions(screen.getByLabelText("Time zone"), [
      "Europe/London",
    ]);
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      name: "May",
      country: "GB",
      time_zone: "Europe/London",
    });
  });

  it("does not save an empty name", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    await user.clear(await screen.findByLabelText("What Zeph calls you"));

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("tells the User when saving the profile fails", async () => {
    apiClient.updatePreferences.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    await user.click(
      await screen.findByRole("button", { name: "Save changes" }),
    );

    expect(
      await screen.findByText("We couldn’t save that. Please try again."),
    ).toBeInTheDocument();
  });

  it("turns User Memory off straight away, with the explanation from Copy", async () => {
    apiClient.updatePreferences.mockResolvedValue({
      ...onboardedUser,
      user_memory_enabled: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const memorySwitch = await screen.findByRole("switch", {
      name: "Remember meaningful details",
    });

    expect(screen.getByText("Edited memory explanation.")).toBeInTheDocument();
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");

    await user.click(memorySwitch);

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      user_memory_enabled: false,
    });
    await vi.waitFor(() =>
      expect(memorySwitch).toHaveAttribute("aria-checked", "false"),
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      `Memory is paused.${seedCopy()["shared.memory_off.paused_body"]}`,
    );
    expect(
      within(screen.getByRole("status")).queryByRole("button"),
    ).not.toBeInTheDocument();
  });

  it("shows Not available on your account with the User Memory switch disabled", async () => {
    apiClient.getMe.mockResolvedValue({
      ...onboardedUser,
      user_memory_available: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const memorySwitch = await screen.findByRole("switch", {
      name: "Remember meaningful details",
    });

    expect(memorySwitch).toBeDisabled();
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Not available on your account")).toBeVisible();
    expect(
      screen.getByText("Memory isn’t available on your account."),
    ).toBeVisible();
    await user.click(memorySwitch);
    expect(apiClient.updatePreferences).not.toHaveBeenCalled();
  });

  it("offers Try again when the account cannot be loaded", async () => {
    apiClient.getMe.mockRejectedValueOnce(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByLabelText("What Zeph calls you"),
    ).toBeInTheDocument();
  });

  it("states the retention period from settings", async () => {
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    expect(
      await screen.findByText(
        "Messages are otherwise kept for 14 days. Quotes Zeph keeps as evidence stay until you delete them.",
      ),
    ).toBeInTheDocument();
  });

  it("words the retention period for one day with the one slot", async () => {
    apiClient.getPlatformContent.mockResolvedValue({
      ...content,
      message_retention_days: 1,
    });
    renderWithQueries(
      <AccountSettings
        copy={{
          ...seedCopy(),
          "account.delete_data.retention_one": "Kept for just {count} day.",
        }}
      />,
    );

    expect(
      await screen.findByText(
        "Kept for just 1 day. Quotes Zeph keeps as evidence stay until you delete them.",
      ),
    ).toBeInTheDocument();
  });

  it("deletes the User's data only after confirming in the dialog", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const yourData = within(
      await screen.findByRole("region", { name: "Delete my data" }),
    );

    await user.click(yourData.getByRole("button", { name: "Delete my data" }));
    const dialog = within(
      screen.getByRole("alertdialog", { name: "Delete my data?" }),
    );
    expect(
      dialog.getByText(
        "Removes your messages, memories and the private notes Zeph keeps. This can’t be undone.",
      ),
    ).toBeVisible();
    expect(apiClient.deleteMyData).not.toHaveBeenCalled();
    await user.click(dialog.getByRole("button", { name: "Delete my data" }));

    expect(apiClient.deleteMyData).toHaveBeenCalledTimes(1);
    expect(await yourData.findByRole("status")).toHaveTextContent(
      "Your data has been deleted.",
    );
    expect(apiClient.deleteAccount).not.toHaveBeenCalled();
  });

  it("keeping my data deletes nothing", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const yourData = within(
      await screen.findByRole("region", { name: "Delete my data" }),
    );

    await user.click(yourData.getByRole("button", { name: "Delete my data" }));
    await user.click(screen.getByRole("button", { name: "Keep my data" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(apiClient.deleteMyData).not.toHaveBeenCalled();
  });

  it("tells the User when deleting their data fails", async () => {
    apiClient.deleteMyData.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const yourData = within(
      await screen.findByRole("region", { name: "Delete my data" }),
    );

    await user.click(yourData.getByRole("button", { name: "Delete my data" }));
    await user.click(
      within(
        screen.getByRole("alertdialog", { name: "Delete my data?" }),
      ).getByRole("button", { name: "Delete my data" }),
    );

    expect(await yourData.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete your data. Please try again.",
    );
  });

  it("deletes the account after confirming in the dialog, then signs out", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const deleteAccount = within(
      await screen.findByRole("region", { name: "Delete account" }),
    );

    await user.click(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    );
    expect(apiClient.deleteAccount).not.toHaveBeenCalled();
    await user.click(
      within(
        screen.getByRole("alertdialog", { name: "Delete your account?" }),
      ).getByRole("button", { name: "Permanently delete account" }),
    );

    expect(apiClient.deleteAccount).toHaveBeenCalledTimes(1);
    await vi.waitFor(() => expect(signOut).toHaveBeenCalledWith("/sign-in"));
    expect(apiClient.deleteMyData).not.toHaveBeenCalled();
  });

  it("keeps the account when the User chooses to", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const deleteAccount = within(
      await screen.findByRole("region", { name: "Delete account" }),
    );

    await user.click(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    );
    await user.click(screen.getByRole("button", { name: "Keep my account" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(apiClient.deleteAccount).not.toHaveBeenCalled();
  });

  it("shows why the last Admin can't delete their account, and stays signed in", async () => {
    apiClient.deleteAccount.mockRejectedValue(
      new ApiError(409, "/api/me", "You’re the only Admin."),
    );
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const deleteAccount = within(
      await screen.findByRole("region", { name: "Delete account" }),
    );

    await user.click(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Permanently delete account" }),
    );

    expect(await deleteAccount.findByRole("alert")).toHaveTextContent(
      "You’re the only Admin.",
    );
    expect(signOut).not.toHaveBeenCalled();
  });

  it("turns Photo Viewing off straight away, with the explanation from Copy", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const photoSwitch = await screen.findByRole("switch", {
      name: "Look at my photos",
    });

    expect(
      screen.getByText(
        "When off, Zeph won’t look at or remember your photos. Every photo is still checked for safety.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("When on, Zeph looks at your photos."),
    ).toBeInTheDocument();
    expect(photoSwitch).toHaveAttribute("aria-checked", "true");

    await user.click(photoSwitch);

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      photo_viewing_enabled: false,
    });
    await vi.waitFor(() =>
      expect(photoSwitch).toHaveAttribute("aria-checked", "false"),
    );
  });

  it("shows Not available on your account with the Photo Viewing switch disabled", async () => {
    apiClient.getMe.mockResolvedValue({
      ...onboardedUser,
      photo_viewing_available: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);
    const photoSwitch = await screen.findByRole("switch", {
      name: "Look at my photos",
    });
    const section = screen.getByRole("region", { name: "Look at my photos" });

    expect(photoSwitch).toBeDisabled();
    expect(photoSwitch).toHaveAttribute("aria-checked", "true");
    expect(
      within(section).getByText("Not available on your account"),
    ).toBeVisible();
    await user.click(photoSwitch);
    expect(apiClient.updatePreferences).not.toHaveBeenCalled();
  });

  it("marks Photo Viewing as changed in chat", async () => {
    apiClient.getMe.mockResolvedValue({
      ...onboardedUser,
      changed_in_chat: { photo_viewing: "2026-11-07T09:00:00Z" },
    });
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    const section = await screen.findByRole("region", {
      name: "Look at my photos",
    });
    expect(
      within(section).getByText("Changed in chat · 7 Nov"),
    ).toBeInTheDocument();
  });

  it("tells the User when changing Photo Viewing fails", async () => {
    apiClient.updatePreferences.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<AccountSettings copy={editedCopy} />);

    await user.click(
      await screen.findByRole("switch", { name: "Look at my photos" }),
    );

    const section = screen.getByRole("region", { name: "Look at my photos" });
    expect(
      await within(section).findByText(
        "We couldn’t change that. Please try again.",
      ),
    ).toBeInTheDocument();
  });

  describe("reads every word from Copy", () => {
    const changedAt = "2026-11-03T02:00:00Z";

    /**
     * Says what words on the page did not come from Copy, leaving out the
     * country and time zone names, which are values.
     *
     * @returns Each piece of text not from Copy.
     */
    function wordsNotFromCopyOnPage(): string[] {
      const words = document.body.cloneNode(true) as HTMLElement;
      words
        .querySelectorAll("option:not([disabled])")
        .forEach((place) => place.remove());
      return wordsNotFromCopy(words);
    }

    async function renderMarked() {
      renderWithQueries(<AccountSettings copy={markedCopy()} />);
      await screen.findByRole("region", {
        name: "⟦account.stickers.heading⟧",
      });
    }

    beforeEach(() => {
      apiClient.getMe.mockResolvedValue({
        ...onboardedUser,
        name: "⟦data⟧",
        email: "⟦data⟧",
        changed_in_chat: {
          time_zone: changedAt,
          user_memory: changedAt,
          photo_viewing: changedAt,
        },
      });
      apiClient.listPersonalStickers.mockResolvedValue([
        {
          id: "laugh",
          emoji: "⟦data⟧",
          note: "⟦data⟧",
          has_image: false,
          kept_at: changedAt,
        },
        {
          id: "plain",
          emoji: null,
          note: "⟦data⟧",
          has_image: false,
          kept_at: changedAt,
        },
      ]);
    });

    it("with everything on, settings changed in chat and stickers kept", async () => {
      await renderMarked();

      expect(screen.getAllByText("⟦account.changed_in_chat⟧")).toHaveLength(3);
      expect(
        await screen.findByRole("button", {
          name: "⟦account.stickers.remove⟧",
        }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", {
          name: "⟦account.stickers.remove_no_emoji⟧",
        }),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
    });

    it("with no email, features off by an Admin and no stickers", async () => {
      apiClient.getMe.mockResolvedValue({
        ...onboardedUser,
        name: "⟦data⟧",
        email: null,
        user_memory_available: false,
        photo_viewing_available: false,
        personal_stickers_available: false,
      });
      apiClient.listPersonalStickers.mockResolvedValue([]);
      await renderMarked();

      expect(screen.getAllByText("⟦account.not_available⟧")).toHaveLength(3);
      expect(
        screen.getByText("⟦account.profile.no_email⟧"),
      ).toBeInTheDocument();
      expect(
        await screen.findByText("⟦account.stickers.empty_title⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
    });

    it("when the profile saves, and when changes fail", async () => {
      apiClient.updatePreferences.mockResolvedValue({
        ...onboardedUser,
        name: "⟦data⟧",
        email: "⟦data⟧",
      });
      const user = userEvent.setup();
      await renderMarked();

      await user.click(
        screen.getByRole("button", { name: "⟦account.profile.save⟧" }),
      );
      expect(
        await screen.findByText("⟦account.profile.saved⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);

      apiClient.updatePreferences.mockRejectedValue(new Error("down"));
      await user.click(
        screen.getByRole("button", { name: "⟦account.profile.save⟧" }),
      );
      await user.click(
        screen.getByRole("switch", { name: "⟦account.memory.title⟧" }),
      );
      expect(
        await screen.findByText("⟦account.profile.save_failed⟧"),
      ).toBeInTheDocument();
      expect(
        await screen.findByText("⟦account.switch_save_failed⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
    });

    it("in the delete dialogs, and when deleting fails or is done", async () => {
      const user = userEvent.setup();
      await renderMarked();
      const words = wordsNotFromCopyOnPage;

      await user.click(
        screen.getByRole("button", { name: "⟦account.delete_data.button⟧" }),
      );
      expect(
        screen.getByRole("alertdialog", {
          name: "⟦account.delete_data.dialog_title⟧",
        }),
      ).toHaveTextContent(
        "⟦account.delete_data.description⟧ ⟦account.delete_data.dialog_body⟧",
      );
      expect(words()).toEqual([]);
      await user.click(
        screen.getByRole("button", {
          name: "⟦account.delete_data.dialog_confirm⟧",
        }),
      );
      expect(
        await screen.findByText("⟦account.delete_data.done⟧"),
      ).toBeInTheDocument();
      expect(words()).toEqual([]);

      apiClient.deleteMyData.mockRejectedValue(new Error("down"));
      apiClient.deleteAccount.mockRejectedValue(new Error("down"));
      await user.click(
        screen.getByRole("button", { name: "⟦account.delete_data.button⟧" }),
      );
      await user.click(
        screen.getByRole("button", {
          name: "⟦account.delete_data.dialog_confirm⟧",
        }),
      );
      await user.click(
        screen.getByRole("button", {
          name: "⟦account.delete_account.button⟧",
        }),
      );
      expect(
        screen.getByRole("alertdialog", {
          name: "⟦account.delete_account.dialog_title⟧",
        }),
      ).toBeInTheDocument();
      expect(words()).toEqual([]);
      await user.click(
        screen.getByRole("button", {
          name: "⟦account.delete_account.dialog_confirm⟧",
        }),
      );
      expect(
        await screen.findByText("⟦account.delete_data.failed⟧"),
      ).toBeInTheDocument();
      expect(
        await screen.findByText("⟦account.delete_account.failed⟧"),
      ).toBeInTheDocument();
      expect(words()).toEqual([]);
    });

    it("while loading, and when loading fails", async () => {
      apiClient.getMe.mockRejectedValue(new Error("down"));
      renderWithQueries(<AccountSettings copy={markedCopy()} />);

      expect(
        screen.getByRole("status", { name: "⟦account.loading⟧" }),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
      expect(
        await screen.findByText("⟦account.load_failed.title⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
    });

    it("while the stickers load, and when they can't", async () => {
      apiClient.listPersonalStickers.mockRejectedValue(new Error("down"));
      renderWithQueries(<AccountSettings copy={markedCopy()} />);

      expect(
        await screen.findByRole("status", {
          name: "⟦account.stickers.loading⟧",
        }),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
      expect(
        await screen.findByText("⟦account.stickers.load_failed_title⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOnPage()).toEqual([]);
    });
  });
});
