import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlatformSettingsForm } from "@/components/PlatformSettingsForm";
import { ApiError, type AdminSettings, type ApiClient } from "@/lib/api-client";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function seeded(value: string | number | boolean) {
  return { value, updated_at: "2026-11-01T00:00:00Z", updated_by: null };
}

const settings: AdminSettings = {
  conversation_quiet_gap_minutes: seeded(60),
  web_search_enabled: seeded(true),
  web_search_daily_limit: seeded(10),
  ai_notice: seeded("I'm an AI."),
  ai_notice_short: seeded("Zeph is an AI."),
  user_memory_explanation: seeded("I can keep details."),
};

describe("PlatformSettingsForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getAdminSettings.mockResolvedValue(settings);
    apiClient.updateAdminSettings.mockImplementation(async (values) => ({
      ...settings,
      conversation_quiet_gap_minutes: {
        value: Number(values.conversation_quiet_gap_minutes ?? 60),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
    }));
  });

  it("shows the quiet gap and the shared wording", async () => {
    render(<PlatformSettingsForm />);

    expect(await screen.findByLabelText("Conversation quiet gap")).toHaveValue(
      60,
    );
    expect(screen.getByLabelText(/^AI notice/)).toHaveValue("I'm an AI.");
    expect(screen.getByLabelText(/Short AI notice/)).toHaveValue(
      "Zeph is an AI.",
    );
    expect(screen.getByLabelText(/Memory explanation/)).toHaveValue(
      "I can keep details.",
    );
    expect(screen.getByText("Using the starting values")).toBeVisible();
  });

  it("saves only the settings that changed", async () => {
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);
    const gap = await screen.findByLabelText("Conversation quiet gap");

    await user.clear(gap);
    await user.type(gap, "45");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      conversation_quiet_gap_minutes: 45,
    });
    expect(await screen.findByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(screen.getByText("Saved")).toBeVisible();
  });

  it("shows web search on, with its daily limit", async () => {
    render(<PlatformSettingsForm />);

    expect(
      await screen.findByRole("switch", { name: "Web search" }),
    ).toHaveAttribute("aria-checked", "true");
    expect(
      screen.getByLabelText("Per-user daily web search limit"),
    ).toHaveValue(10);
  });

  it("turns web search off, hiding the limit, and saves it", async () => {
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);
    const webSearch = await screen.findByRole("switch", { name: "Web search" });

    await user.click(webSearch);

    expect(webSearch).toHaveAttribute("aria-checked", "false");
    expect(
      screen.queryByLabelText("Per-user daily web search limit"),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Save settings" }));
    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      web_search_enabled: false,
    });
  });

  it("saves a new daily web search limit as a number", async () => {
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);
    const limit = await screen.findByLabelText(
      "Per-user daily web search limit",
    );

    await user.clear(limit);
    await user.type(limit, "0");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      web_search_daily_limit: 0,
    });
  });

  it("won't save a quiet gap that is not a whole number", async () => {
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);
    const gap = await screen.findByLabelText("Conversation quiet gap");

    await user.clear(gap);

    expect(
      screen.getByRole("button", { name: "Save settings" }),
    ).toBeDisabled();
  });

  it("shows why the backend refused a value", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/settings",
        "The Conversation quiet gap must be a whole number from 5 to 1440.",
      ),
    );
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);
    const gap = await screen.findByLabelText("Conversation quiet gap");

    await user.clear(gap);
    await user.type(gap, "2");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(
      await screen.findByText(
        "The Conversation quiet gap must be a whole number from 5 to 1440.",
      ),
    ).toBeVisible();
  });

  it("discards unsaved changes", async () => {
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);
    const notice = await screen.findByLabelText(/^AI notice/);

    await user.type(notice, " Extra.");
    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(notice).toHaveValue("I'm an AI.");
  });

  it("says so when saving fails", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);

    await user.type(await screen.findByLabelText(/^AI notice/), " Extra.");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(
      await screen.findByText(
        "Couldn’t save. The platform keeps running on the last saved values.",
      ),
    ).toBeVisible();
  });

  it("offers Try again when settings cannot be loaded", async () => {
    apiClient.getAdminSettings
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(settings);
    const user = userEvent.setup();
    render(<PlatformSettingsForm />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByLabelText("Conversation quiet gap"),
    ).toBeInTheDocument();
  });
});
