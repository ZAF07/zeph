import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserFeaturesPanel } from "@/components/UserFeaturesPanel";
import type { AdminUser, ApiClient, UserFeatureStatus } from "@/lib/api-client";

const apiClient = {
  listUserFeatures: vi.fn<ApiClient["listUserFeatures"]>(),
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
};

const webSearch: UserFeatureStatus = {
  feature: "web_search",
  name: "Web Search",
  works: true,
  reason: "on_for_everyone",
  switch: "default",
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

describe("UserFeaturesPanel", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listUserFeatures.mockResolvedValue([webSearch]);
  });

  it("shows each Feature's switch for the User and whether it works", async () => {
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    const dialog = await screen.findByRole("dialog", {
      name: "Features for Ren Okafor",
    });
    expect(apiClient.listUserFeatures).toHaveBeenCalledWith("ren");
    expect(within(dialog).getByText("ren@example.com")).toBeVisible();
    const row = within(rowFor("Web Search"));
    expect(row.getByRole("button", { name: "Default" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(row.getByRole("button", { name: "On" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(row.getByText("On: on for everyone")).toBeVisible();
    expect(row.queryByText(/Changed/)).not.toBeInTheDocument();
  });

  it.each([
    ["off_for_everyone", "default", "Off: turned off for everyone"],
    ["off_for_user", "off", "Off: turned off for this User"],
    ["on_for_user", "on", "On: turned on for this User"],
    ["turned_off_by_user", "default", "Off: the User turned it off"],
  ] as const)("explains %s", async (reason, featureSwitch, text) => {
    apiClient.listUserFeatures.mockResolvedValue([
      {
        ...webSearch,
        works: reason === "on_for_user",
        reason,
        switch: featureSwitch,
      },
    ]);
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    expect(await screen.findByText(text)).toBeVisible();
  });

  it("shows who last changed the switch for the User, and when", async () => {
    apiClient.listUserFeatures.mockResolvedValue([
      {
        ...webSearch,
        works: false,
        reason: "off_for_user",
        switch: "off",
        changed_by_email: "maya@example.com",
        changed_at: "2026-11-13T09:00:00Z",
      },
    ]);
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    expect(
      await screen.findByText(/^Changed 13 Nov, .+ by maya@example.com$/),
    ).toBeVisible();
  });

  it("turns a Feature off for the User", async () => {
    apiClient.setFeatureForUser.mockResolvedValue({
      ...webSearch,
      works: false,
      reason: "off_for_user",
      switch: "off",
      changed_by_email: "maya@example.com",
      changed_at: "2026-11-13T09:00:00Z",
    });
    const user = userEvent.setup();
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    await screen.findByText("Web Search");
    await user.click(
      within(rowFor("Web Search")).getByRole("button", { name: "Off" }),
    );

    expect(apiClient.setFeatureForUser).toHaveBeenCalledWith(
      "ren",
      "web_search",
      "off",
    );
    const row = within(rowFor("Web Search"));
    expect(row.getByRole("button", { name: "Off" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(row.getByText("Off: turned off for this User")).toBeVisible();
  });

  it("shows Stickers and Knowledge and turns Knowledge back on for the User", async () => {
    apiClient.listUserFeatures.mockResolvedValue([
      webSearch,
      {
        ...webSearch,
        feature: "stickers",
        name: "Stickers",
        works: false,
        reason: "off_for_everyone",
      },
      {
        ...webSearch,
        feature: "knowledge",
        name: "Knowledge",
        works: false,
        reason: "off_for_user",
        switch: "off",
        changed_by_email: "maya@example.com",
        changed_at: "2026-11-13T09:00:00Z",
      },
    ]);
    apiClient.setFeatureForUser.mockResolvedValue({
      ...webSearch,
      feature: "knowledge",
      name: "Knowledge",
      works: true,
      reason: "on_for_user",
      switch: "on",
      changed_by_email: "owner@example.com",
      changed_at: "2026-11-13T10:00:00Z",
    });
    const user = userEvent.setup();
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    await screen.findByText("Stickers");
    const stickers = within(rowFor("Stickers"));
    const knowledge = within(rowFor("Knowledge"));
    expect(stickers.getByText("Off: turned off for everyone")).toBeVisible();
    expect(knowledge.getByText("Off: turned off for this User")).toBeVisible();
    expect(
      knowledge.getByText(/^Changed 13 Nov, .+ by maya@example.com$/),
    ).toBeVisible();

    await user.click(knowledge.getByRole("button", { name: "On" }));

    expect(apiClient.setFeatureForUser).toHaveBeenCalledWith(
      "ren",
      "knowledge",
      "on",
    );
    expect(knowledge.getByRole("button", { name: "On" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(
      await knowledge.findByText("On: turned on for this User"),
    ).toBeVisible();
    expect(stickers.getByText("Off: turned off for everyone")).toBeVisible();
  });

  it("keeps the switch as it was when a change fails", async () => {
    apiClient.setFeatureForUser.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    await screen.findByText("Web Search");
    await user.click(
      within(rowFor("Web Search")).getByRole("button", { name: "On" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t change Web Search for Ren Okafor. It is still default.",
    );
    expect(
      within(rowFor("Web Search")).getByRole("button", { name: "Default" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("offers Try again when the Features can't be loaded", async () => {
    apiClient.listUserFeatures
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValueOnce([webSearch]);
    const user = userEvent.setup();
    render(<UserFeaturesPanel user={ren} onClose={() => {}} />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Web Search")).toBeVisible();
  });

  it("closes with Close or Escape", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<UserFeaturesPanel user={ren} onClose={onClose} />);

    await screen.findByText("Web Search");
    await user.click(screen.getByRole("button", { name: "Close" }));
    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
