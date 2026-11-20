import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserFeatureSwitches } from "@/components/UserFeatureSwitches";
import type {
  AdminUser,
  ApiClient,
  FeatureSwitch,
  UserFeatureStatus,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listUserFeatures: vi.fn<ApiClient["listUserFeatures"]>(),
  listFeatures: vi.fn<ApiClient["listFeatures"]>(),
  setFeatureForUser: vi.fn<ApiClient["setFeatureForUser"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const ren: AdminUser = {
  id: "ren",
  name: "Ren Okafor",
  email: "ren@example.com",
  role: "user",
  signed_up_at: "2026-10-05T09:00:00Z",
  telegram_connected: true,
  conversation_count: 3,
  messages_sent: 20,
  life_thread_count: 0,
  move_outcome_count: 0,
  has_portrait: false,
  confirmed_pattern_count: 0,
};

const webSearch: UserFeatureStatus = {
  feature: "web_search",
  name: "Web search",
  works: true,
  reason: "on_for_everyone",
  switch: "default",
  changed_by_email: null,
  changed_at: null,
};

const stickers: UserFeatureStatus = {
  ...webSearch,
  feature: "stickers",
  name: "Stickers",
};

const knowledge: UserFeatureStatus = {
  ...webSearch,
  feature: "knowledge",
  name: "Knowledge",
  works: false,
  reason: "off_for_everyone",
};

/** Builds everyone's switch for a Feature. */
function everyone(feature: UserFeatureStatus, on: boolean): FeatureSwitch {
  return {
    feature: feature.feature,
    name: feature.name,
    description: "",
    on,
    changed_by_email: null,
    changed_at: null,
  };
}

describe("UserFeatureSwitches", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listUserFeatures.mockResolvedValue({
      features: [webSearch, stickers, knowledge],
      personal_sticker_count: 4,
    });
    apiClient.listFeatures.mockResolvedValue([
      everyone(webSearch, true),
      everyone(stickers, true),
      everyone(knowledge, false),
    ]);
  });

  it("shows each Feature's switch, whether it works and why, and the sticker count", async () => {
    renderWithQueries(<UserFeatureSwitches user={ren} />);

    expect(
      await screen.findByRole("switch", { name: "Web search for this user" }),
    ).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Works: on for everyone")).toBeInTheDocument();
    expect(
      screen.getByText("Works · 4 personal stickers kept"),
    ).toBeInTheDocument();
    expect(screen.getByText("Off for everyone")).toBeInTheDocument();
    expect(
      screen.getByRole("switch", { name: "Knowledge for this user" }),
    ).toHaveAttribute("aria-checked", "false");
  });

  it("turns a Feature off for the User when it is on for everyone", async () => {
    apiClient.setFeatureForUser.mockResolvedValue({
      ...webSearch,
      works: false,
      reason: "off_for_user",
      switch: "off",
    });
    const user = userEvent.setup();
    renderWithQueries(<UserFeatureSwitches user={ren} />);

    await user.click(
      await screen.findByRole("switch", { name: "Web search for this user" }),
    );

    expect(apiClient.setFeatureForUser).toHaveBeenCalledWith(
      "ren",
      "web_search",
      "off",
    );
    expect(await screen.findByText("Off for this user")).toBeInTheDocument();
    expect(
      screen.getByRole("switch", { name: "Web search for this user" }),
    ).toHaveAttribute("aria-checked", "false");
  });

  it("goes back to Default when the switch matches everyone's again", async () => {
    apiClient.listUserFeatures.mockResolvedValue({
      features: [
        {
          ...knowledge,
          works: true,
          reason: "on_for_user",
          switch: "on",
          changed_by_email: "zaf@example.com",
          changed_at: "2026-11-13T09:00:00Z",
        },
      ],
      personal_sticker_count: 0,
    });
    apiClient.setFeatureForUser.mockResolvedValue(knowledge);
    const user = userEvent.setup();
    renderWithQueries(<UserFeatureSwitches user={ren} />);

    expect(
      await screen.findByText(/^Changed 13 Nov, .+ by zaf@example\.com$/),
    ).toBeInTheDocument();
    await user.click(
      screen.getByRole("switch", { name: "Knowledge for this user" }),
    );

    expect(apiClient.setFeatureForUser).toHaveBeenCalledWith(
      "ren",
      "knowledge",
      "default",
    );
  });

  it("keeps the switch as it was when a change fails", async () => {
    apiClient.setFeatureForUser.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<UserFeatureSwitches user={ren} />);

    await user.click(
      await screen.findByRole("switch", { name: "Web search for this user" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t change Web search for Ren Okafor. It is still on.",
    );
    expect(
      screen.getByRole("switch", { name: "Web search for this user" }),
    ).toHaveAttribute("aria-checked", "true");
  });

  it("offers Try again when the Features can't be loaded", async () => {
    apiClient.listUserFeatures
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue({ features: [webSearch], personal_sticker_count: 0 });
    const user = userEvent.setup();
    renderWithQueries(<UserFeatureSwitches user={ren} />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("switch", { name: "Web search for this user" }),
    ).toBeInTheDocument();
  });
});
