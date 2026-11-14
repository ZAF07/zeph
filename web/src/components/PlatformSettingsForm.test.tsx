import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlatformSettingsForm } from "@/components/PlatformSettingsForm";
import { ApiError, type AdminSettings, type ApiClient } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function seeded(value: string | number) {
  return { value, updated_at: "2026-11-01T00:00:00Z", updated_by: null };
}

const settings: AdminSettings = {
  conversation_quiet_gap_minutes: seeded(60),
  message_wait_seconds: seeded(4),
  typing_repeat_seconds: seeded(4),
  web_search_daily_limit: seeded(10),
  ai_notice: seeded("I'm an AI."),
  ai_notice_short: seeded("Zeph is an AI."),
  user_memory_explanation: seeded("I can keep details."),
  check_in_ignore_threshold: seeded(3),
  check_in_fewer_message: seeded("Would you like fewer check-ins?"),
  daily_message_limit: seeded(200),
  daily_limit_reply: seeded("I'm wiped for today, talk tomorrow?"),
  message_retention_days: seeded(30),
  older_summaries_per_reply: seeded(3),
  older_summaries_closeness_percent: seeded(68),
  life_threads_per_reply: seeded(3),
  life_threads_closeness_percent: seeded(68),
  life_thread_brushed_off_wait_days: seeded(14),
  curiosities_per_conversation: seeded(1),
  curiosities_waiting_limit: seeded(10),
  knowledge_closeness_percent: seeded(60),
  photo_retry_count: seeded(2),
  photo_album_max_photos: seeded(5),
  personal_stickers_limit: seeded(30),
  sticker_adding_quiet_gap_minutes: seeded(5),
  photo_not_viewed_note: seeded("Say the photo didn't come through."),
  photo_viewing_off_note: seeded("Say you didn't look at the photo."),
  photo_viewing_explanation: seeded("When off, Zeph won't look at photos."),
  onboarding_unfinished_reply: seeded("Finish setting up: {dashboard_url}"),
  memory_paused_note: seeded("**Memory is paused.** Still used."),
  memory_not_available_note: seeded("**Memory isn’t available.** Still used."),
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
    renderWithQueries(<PlatformSettingsForm />);

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
    expect(screen.getByLabelText(/Memory is paused” note/)).toHaveValue(
      "**Memory is paused.** Still used.",
    );
    expect(screen.getByLabelText(/Memory isn’t available” note/)).toHaveValue(
      "**Memory isn’t available.** Still used.",
    );
    expect(screen.getByText("Using the starting values")).toBeVisible();
  });

  it("saves only the settings that changed", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
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

  it("shows and saves the sticker adding quiet gap", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const gap = await screen.findByLabelText("Sticker adding quiet gap");
    expect(gap).toHaveValue(5);

    await user.clear(gap);
    await user.type(gap, "10");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      sticker_adding_quiet_gap_minutes: 10,
    });
  });

  it("shows and saves the Check-in ignore threshold and fewer message", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const threshold = await screen.findByLabelText("Ignore threshold");
    expect(threshold).toHaveValue(3);
    const message = screen.getByLabelText(/Would you like fewer\?” message/);
    expect(message).toHaveValue("Would you like fewer check-ins?");

    await user.clear(threshold);
    await user.type(threshold, "5");
    await user.clear(message);
    await user.type(message, "Fewer of these?");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      check_in_ignore_threshold: 5,
      check_in_fewer_message: "Fewer of these?",
    });
  });

  it("shows and saves the daily message limit and limit-reached reply", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const limit = await screen.findByLabelText("Daily message limit");
    expect(limit).toHaveValue(200);
    expect(
      screen.getByText("Per User. Safety replies never count toward it."),
    ).toBeVisible();
    const reply = screen.getByLabelText(/Limit-reached reply/);
    expect(reply).toHaveValue("I'm wiped for today, talk tomorrow?");

    await user.clear(limit);
    await user.type(limit, "60");
    await user.clear(reply);
    await user.type(reply, "Out of steam, talk tomorrow?");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      daily_message_limit: 60,
      daily_limit_reply: "Out of steam, talk tomorrow?",
    });
  });

  it("shows and saves the older Conversation limit and closeness bar", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const most = await screen.findByLabelText(
      "Most older Conversations per reply",
    );
    const bar = screen.getByLabelText("Older Conversation closeness bar");
    expect(most).toHaveValue(3);
    expect(bar).toHaveValue(68);

    await user.clear(most);
    await user.type(most, "5");
    await user.clear(bar);
    await user.type(bar, "72");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      older_summaries_per_reply: 5,
      older_summaries_closeness_percent: 72,
    });
  });

  it("shows and saves the Life Thread number, closeness bar and wait", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const most = await screen.findByLabelText("Most Life Threads per reply");
    const bar = screen.getByLabelText("Life Thread closeness bar");
    const wait = screen.getByLabelText("Wait after a brushed-off Life Thread");
    expect(most).toHaveValue(3);
    expect(bar).toHaveValue(68);
    expect(wait).toHaveValue(14);

    await user.clear(most);
    await user.type(most, "2");
    await user.clear(bar);
    await user.type(bar, "70");
    await user.clear(wait);
    await user.type(wait, "21");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      life_threads_per_reply: 2,
      life_threads_closeness_percent: 70,
      life_thread_brushed_off_wait_days: 21,
    });
  });

  it("shows and saves the Curiosity limits", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const raised = await screen.findByLabelText(
      "Most Curiosities raised per Conversation",
    );
    const waiting = screen.getByLabelText("Most Curiosities waiting at once");
    expect(raised).toHaveValue(1);
    expect(waiting).toHaveValue(10);

    await user.clear(raised);
    await user.type(raised, "2");
    await user.clear(waiting);
    await user.type(waiting, "20");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      curiosities_per_conversation: 2,
      curiosities_waiting_limit: 20,
    });
  });

  it("shows and saves the Knowledge closeness bar", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const bar = await screen.findByLabelText("Knowledge closeness bar");
    expect(bar).toHaveValue(60);

    await user.clear(bar);
    await user.type(bar, "70");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      knowledge_closeness_percent: 70,
    });
  });

  it("shows and saves the finish-onboarding-first reply", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const reply = await screen.findByLabelText(
      /“Finish onboarding first” reply/,
    );
    expect(reply).toHaveValue("Finish setting up: {dashboard_url}");

    await user.clear(reply);
    await user.type(reply, "Set up first: {{dashboard_url}");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      onboarding_unfinished_reply: "Set up first: {dashboard_url}",
    });
  });

  it("shows and saves the photo retries and the didn't-come-through note", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const retries = await screen.findByLabelText("Photo retries");
    expect(retries).toHaveValue(2);
    expect(screen.getByRole("region", { name: "Photos" })).toContainElement(
      retries,
    );
    const note = screen.getByLabelText(/Didn’t come through” note/);
    expect(note).toHaveValue("Say the photo didn't come through.");

    await user.clear(retries);
    await user.type(retries, "3");
    await user.clear(note);
    await user.type(note, "It didn't load.");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      photo_retry_count: 3,
      photo_not_viewed_note: "It didn't load.",
    });
  });

  it("shows and saves the message wait in its Conversations section", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const wait = await screen.findByLabelText("Message wait");
    expect(wait).toHaveValue(4);
    expect(
      screen.getByRole("region", { name: "Conversations" }),
    ).toContainElement(wait);
    expect(screen.queryByLabelText("Album wait")).not.toBeInTheDocument();

    await user.clear(wait);
    await user.type(wait, "6");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      message_wait_seconds: 6,
    });
  });

  it("shows and saves the typing repeat in its Conversations section", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const repeat = await screen.findByLabelText("Typing repeat");
    expect(repeat).toHaveValue(4);
    expect(
      screen.getByRole("region", { name: "Conversations" }),
    ).toContainElement(repeat);

    await user.clear(repeat);
    await user.type(repeat, "3");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      typing_repeat_seconds: 3,
    });
  });

  it("shows and saves the most photos per album", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const most = await screen.findByLabelText("Most photos per album");
    expect(most).toHaveValue(5);
    expect(screen.getByRole("region", { name: "Photos" })).toContainElement(
      most,
    );

    await user.clear(most);
    await user.type(most, "8");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      photo_album_max_photos: 8,
    });
  });

  it("shows and saves the message retention in its Data section", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const retention = await screen.findByLabelText("Message retention");
    expect(retention).toHaveValue(30);
    expect(screen.getByRole("region", { name: "Data" })).toContainElement(
      retention,
    );
    expect(retention).toHaveAccessibleDescription(
      "Shortening applies to existing messages within a minute.",
    );

    await user.clear(retention);
    await user.type(retention, "14");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      message_retention_days: 14,
    });
  });

  it("shows the web search daily limit but no Web Search switch", async () => {
    renderWithQueries(<PlatformSettingsForm />);

    expect(
      await screen.findByLabelText("Per-user daily web search limit"),
    ).toHaveValue(10);
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
  });

  it("saves a new daily web search limit as a number", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
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
    renderWithQueries(<PlatformSettingsForm />);
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
    renderWithQueries(<PlatformSettingsForm />);
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
    renderWithQueries(<PlatformSettingsForm />);
    const notice = await screen.findByLabelText(/^AI notice/);

    await user.type(notice, " Extra.");
    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(notice).toHaveValue("I'm an AI.");
  });

  it("says so when saving fails", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);

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
    renderWithQueries(<PlatformSettingsForm />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByLabelText("Conversation quiet gap"),
    ).toBeInTheDocument();
  });

  it("shows and saves the Photo Viewing off note and explanation", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const note = await screen.findByLabelText(/Photo Viewing off” note/);
    const explanation = screen.getByLabelText(/Photo Viewing explanation/);
    expect(note).toHaveValue("Say you didn't look at the photo.");
    expect(explanation).toHaveValue("When off, Zeph won't look at photos.");

    await user.clear(note);
    await user.type(note, "You didn't look.");
    await user.clear(explanation);
    await user.type(explanation, "Off means no looking.");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      photo_viewing_off_note: "You didn't look.",
      photo_viewing_explanation: "Off means no looking.",
    });
  });
});
