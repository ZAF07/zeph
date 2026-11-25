import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlatformSettingsForm } from "@/components/PlatformSettingsForm";
import {
  ApiError,
  type AdminSettings,
  type ApiClient,
  type SettingValue,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function seeded(value: SettingValue, hint = "") {
  return {
    label: "",
    hint,
    value,
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  };
}

const settings: AdminSettings = {
  conversation_quiet_gap_minutes: seeded(60),
  message_wait_seconds: seeded(4),
  message_wait_finished_seconds: seeded(
    2,
    "Seconds Zeph waits for more when the User’s last text reads finished.",
  ),
  message_wait_trailing_seconds: seeded(
    12,
    "Seconds Zeph waits for more when the User’s last text ends unfinished.",
  ),
  message_wait_cap_seconds: seeded(
    20,
    "Most seconds Zeph waits from the first text of a Message.",
  ),
  message_wait_long_text_words: seeded(
    15,
    "How many words a text needs to read finished.",
  ),
  message_wait_trailing_words: seeded(
    ["and", "so", "ok so"],
    "Words that make a text trail off when they end it.",
  ),
  typing_repeat_seconds: seeded(4),
  web_search_daily_limit: seeded(10),
  check_in_ignore_threshold: seeded(3),
  check_in_hours_between: seeded({
    weekly: 168,
    few_times_a_week: 56,
    most_days: 24,
    a_few_times_a_day: 6,
  }),
  check_in_fewer_message: seeded("Would you like fewer check-ins?"),
  daily_message_limit: seeded(
    200,
    "Messages a User can send per day before the Reply gate stops replying.",
  ),
  daily_limit_reply: seeded(
    "I'm wiped for today, talk tomorrow?",
    "Sent in Telegram by the Reply gate when a User hits the daily limit.",
  ),
  message_retention_days: seeded(30),
  recent_messages_hours: seeded(
    24,
    "Hours of messages, across Conversations, that every reply sees.",
  ),
  recent_messages_cap: seeded(400),
  older_summaries_per_reply: seeded(3),
  older_summaries_closeness_percent: seeded(68),
  life_threads_per_reply: seeded(10),
  life_threads_texts_to_search: seeded(
    8,
    "How many of the User’s latest texts Recall searches Life Threads on.",
  ),
  life_threads_closeness_percent: seeded(68),
  life_thread_brushed_off_wait_days: seeded(14),
  pattern_closeness_percent: seeded(
    52,
    "How close in meaning a Pattern must be for Recall to bring it to mind with no Thread.",
  ),
  pattern_weak_sign_points: seeded(30),
  pattern_moderate_sign_points: seeded(70),
  pattern_strong_sign_points: seeded(140),
  pattern_real_story_percent: seeded(100),
  pattern_reported_habit_percent: seeded(70),
  pattern_what_if_percent: seeded(40),
  pattern_own_opinion_percent: seeded(30),
  pattern_unclear_percent: seeded(25),
  pattern_half_life_days: seeded(
    75,
    "After this many days an Observation counts half.",
  ),
  pattern_people_per_situation: seeded(3),
  pattern_suspected_situations: seeded(2),
  pattern_suspected_points: seeded(100),
  pattern_closed_under_points: seeded(-150),
  agenda_size: seeded(
    3,
    "How many of a User's suspected Patterns Zeph explores at once.",
  ),
  exploration_wait_days: seeded(3),
  exploration_rest_after_tries: seeded(4),
  thought_experiments_per_pattern_per_week: seeded(1),
  pattern_ready_situations: seeded(3),
  pattern_ready_conversations: seeded(2),
  pattern_ready_points: seeded(300, "The lowest score to be shared."),
  pattern_ready_against_under_points: seeded(100),
  pattern_safeguard_quiet_days: seeded(14),
  pattern_exclusion_summary_days: seeded(7),
  pattern_ruled_out_topics: seeded(
    ["abuse", "self-harm or suicide"],
    "Topics no Pattern is drawn or shared from unless the User raised them.",
  ),
  familiarity_conversations: seeded(5),
  familiarity_life_threads: seeded(3),
  familiarity_real_stories: seeded(0),
  starter_thought_experiments: seeded(4),
  starter_thought_experiment_days: seeded(14),
  starter_thought_experiments_per_conversation: seeded(1),
  unmatched_grouping_closeness_percent: seeded(80),
  move_outcomes_per_understanding: seeded(3),
  move_outcomes_closeness_percent: seeded(65),
  curiosities_per_conversation: seeded(1),
  curiosities_per_reply: seeded(
    1,
    "Most Curiosities raised per Conversation still caps it.",
  ),
  curiosity_held_when_asking_why: seeded(
    true,
    "When on, a reply that asks why asks no Curiosity too.",
  ),
  curiosities_waiting_limit: seeded(10),
  curiosity_check_ins_per_week: seeded(1),
  curiosity_replies_between: seeded(3),
  follow_ups_per_conversation: seeded(3),
  curiosity_brush_offs_to_back_off: seeded(2),
  curiosity_back_off_days: seeded(3),
  knowledge_closeness_percent: seeded(60),
  photo_retry_count: seeded(2),
  photo_album_max_photos: seeded(5),
  personal_stickers_limit: seeded(30),
  sticker_adding_quiet_gap_minutes: seeded(5),
  photo_not_viewed_note: seeded("Say the photo didn't come through."),
  photo_viewing_off_note: seeded("Say you didn't look at the photo."),
  onboarding_unfinished_reply: seeded("Finish setting up: {dashboard_url}"),
  memory_off_chat_line: seeded("Nothing is deleted."),
  data_deleted_reply: seeded("Done, all deleted."),
};

describe("PlatformSettingsForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getAdminSettings.mockResolvedValue(settings);
    apiClient.updateAdminSettings.mockImplementation(async (values) => ({
      ...settings,
      conversation_quiet_gap_minutes: {
        hint: "",
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
    expect(screen.getByLabelText(/“Memory off” line in chat/)).toHaveValue(
      "Nothing is deleted.",
    );
    expect(screen.getAllByText("Using the starting values")[0]).toBeVisible();
  });

  it("leaves the website wording to the Copy page", async () => {
    renderWithQueries(<PlatformSettingsForm />);

    await screen.findByLabelText("Conversation quiet gap");
    for (const label of [
      /AI notice/,
      /Memory explanation/,
      /Photo Viewing explanation/,
      /Memory is paused/,
      /Memory isn’t available/,
      /“Delete my data” description/,
    ]) {
      expect(screen.queryByLabelText(label)).not.toBeInTheDocument();
    }
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
    expect(screen.getByText("Saved.")).toBeVisible();
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

  it("shows each frequency's Check-in gap and saves them together", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const fewTimesADay = await screen.findByLabelText(
      "Gap for “A few times a day”",
    );
    expect(fewTimesADay).toHaveValue(6);
    expect(screen.getByLabelText("Gap for “Weekly”")).toHaveValue(168);
    expect(screen.getByLabelText("Gap for “A few times a week”")).toHaveValue(
      56,
    );
    expect(screen.getByLabelText("Gap for “Most days”")).toHaveValue(24);

    await user.clear(fewTimesADay);
    await user.type(fewTimesADay, "4");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      check_in_hours_between: {
        weekly: 168,
        few_times_a_week: 56,
        most_days: 24,
        a_few_times_a_day: 4,
      },
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
      screen.getByText(
        "Messages a User can send per day before the Reply gate stops replying.",
      ),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Sent in Telegram by the Reply gate when a User hits the daily limit.",
      ),
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

  it("shows and saves the Life Thread number, texts, closeness bar and wait", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const most = await screen.findByLabelText("Most Life Threads in mind");
    const texts = screen.getByLabelText("Texts searched for Life Threads");
    const bar = screen.getByLabelText("Life Thread closeness bar");
    const wait = screen.getByLabelText("Wait after a brushed-off Life Thread");
    expect(most).toHaveValue(10);
    expect(texts).toHaveValue(8);
    expect(bar).toHaveValue(68);
    expect(wait).toHaveValue(14);
    expect(
      screen.getByText(
        "How many of the User’s latest texts Recall searches Life Threads on.",
      ),
    ).toBeVisible();
    expect(screen.getByRole("region", { name: "Memory" })).toContainElement(
      texts,
    );

    await user.clear(most);
    await user.type(most, "20");
    await user.clear(texts);
    await user.type(texts, "12");
    await user.clear(bar);
    await user.type(bar, "70");
    await user.clear(wait);
    await user.type(wait, "21");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      life_threads_per_reply: 20,
      life_threads_texts_to_search: 12,
      life_threads_closeness_percent: 70,
      life_thread_brushed_off_wait_days: 21,
    });
  });

  it("shows and saves the Pattern closeness bar, with its hint", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const bar = await screen.findByLabelText("Pattern closeness bar");
    expect(bar).toHaveValue(52);
    expect(
      screen.getByText(
        "How close in meaning a Pattern must be for Recall to bring it to mind with no Thread.",
      ),
    ).toBeVisible();
    expect(screen.getByRole("region", { name: "Memory" })).toContainElement(
      bar,
    );

    await user.clear(bar);
    await user.type(bar, "58");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      pattern_closeness_percent: 58,
    });
  });

  it("shows and saves the Move Outcome number and closeness bar", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const most = await screen.findByLabelText(
      "Most Move Outcomes per Understanding",
    );
    const bar = screen.getByLabelText("Move Outcome closeness bar");
    expect(most).toHaveValue(3);
    expect(bar).toHaveValue(65);

    await user.clear(most);
    await user.type(most, "5");
    await user.clear(bar);
    await user.type(bar, "70");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      move_outcomes_per_understanding: 5,
      move_outcomes_closeness_percent: 70,
    });
  });

  it("shows and saves the Curiosity limits", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const raised = await screen.findByLabelText(
      "Most Curiosities raised per Conversation",
    );
    const waiting = screen.getByLabelText("Most Curiosities waiting at once");
    const perWeek = screen.getByLabelText("Most Curiosity Check-ins per week");
    expect(raised).toHaveValue(1);
    expect(waiting).toHaveValue(10);
    expect(perWeek).toHaveValue(1);

    await user.clear(raised);
    await user.type(raised, "2");
    await user.clear(waiting);
    await user.type(waiting, "20");
    await user.clear(perWeek);
    await user.type(perWeek, "3");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      curiosities_per_conversation: 2,
      curiosities_waiting_limit: 20,
      curiosity_check_ins_per_week: 3,
    });
  });

  it("shows and saves the Curiosities per reply and holding one back, with hints", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const perReply = await screen.findByLabelText("Most Curiosities per reply");
    const held = screen.getByRole("switch", {
      name: "Hold a Curiosity when the reply asks why",
    });
    expect(perReply).toHaveValue(1);
    expect(held).toHaveAttribute("aria-checked", "true");
    expect(
      screen.getByText(
        "Most Curiosities raised per Conversation still caps it.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("When on, a reply that asks why asks no Curiosity too."),
    ).toBeInTheDocument();

    await user.clear(perReply);
    await user.type(perReply, "2");
    await user.click(held);
    expect(held).toHaveAttribute("aria-checked", "false");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      curiosities_per_reply: 2,
      curiosity_held_when_asking_why: false,
    });
  });

  it("shows and saves the Curiosity pace and backing off", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const between = await screen.findByLabelText(
      "Fewest replies between Curiosities",
    );
    const followUps = screen.getByLabelText(
      "Most follow-up questions per Conversation",
    );
    const brushOffs = screen.getByLabelText("Brush-offs before backing off");
    const days = screen.getByLabelText("Days of doubled spacing");
    expect(between).toHaveValue(3);
    expect(followUps).toHaveValue(3);
    expect(brushOffs).toHaveValue(2);
    expect(days).toHaveValue(3);

    await user.clear(between);
    await user.type(between, "4");
    await user.clear(followUps);
    await user.type(followUps, "2");
    await user.clear(brushOffs);
    await user.type(brushOffs, "3");
    await user.clear(days);
    await user.type(days, "5");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      curiosity_replies_between: 4,
      follow_ups_per_conversation: 2,
      curiosity_brush_offs_to_back_off: 3,
      curiosity_back_off_days: 5,
    });
  });

  it("shows and saves the Pattern scoring numbers, a negative floor too", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const halfLife = await screen.findByLabelText("Pattern evidence half-life");
    const floor = screen.getByLabelText("Score that closes a Pattern");
    expect(halfLife).toHaveValue(75);
    expect(floor).toHaveValue(-150);
    expect(screen.getByLabelText("Points for a strong sign")).toHaveValue(140);
    expect(screen.getByLabelText("Unclear counts")).toHaveValue(25);
    expect(screen.getByLabelText("Situations to be suspected")).toHaveValue(2);
    expect(
      screen.getByText("After this many days an Observation counts half."),
    ).toBeInTheDocument();

    await user.clear(halfLife);
    await user.type(halfLife, "60");
    await user.clear(floor);
    await user.type(floor, "-200");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      pattern_half_life_days: 60,
      pattern_closed_under_points: -200,
    });
  });

  it("shows and saves the Agenda numbers in the Patterns section", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const size = await screen.findByLabelText("Explorations on the Agenda");
    const wait = screen.getByLabelText("Wait after a try with nothing");
    const rest = screen.getByLabelText("Tries with nothing before resting");
    expect(size).toHaveValue(3);
    expect(wait).toHaveValue(3);
    expect(rest).toHaveValue(4);
    expect(screen.getByRole("region", { name: "Patterns" })).toContainElement(
      size,
    );
    expect(
      screen.getByText(
        "How many of a User's suspected Patterns Zeph explores at once.",
      ),
    ).toBeInTheDocument();

    await user.clear(size);
    await user.type(size, "2");
    await user.clear(rest);
    await user.type(rest, "5");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      agenda_size: 2,
      exploration_rest_after_tries: 5,
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
    const wait = await screen.findByLabelText("Wait after any other text");
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

  it("shows and saves the finished and trailing waits and the long text, with hints", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const finished = await screen.findByLabelText("Wait after a finished text");
    const trailing = screen.getByLabelText("Wait after a trailing text");
    const longText = screen.getByLabelText("Long text");
    const conversations = screen.getByRole("region", { name: "Conversations" });
    expect(finished).toHaveValue(2);
    expect(trailing).toHaveValue(12);
    expect(longText).toHaveValue(15);
    for (const field of [finished, trailing, longText]) {
      expect(conversations).toContainElement(field);
    }
    expect(
      screen.getByText(
        "Seconds Zeph waits for more when the User’s last text ends unfinished.",
      ),
    ).toBeVisible();

    await user.clear(finished);
    await user.type(finished, "3");
    await user.clear(trailing);
    await user.type(trailing, "20");
    await user.clear(longText);
    await user.type(longText, "10");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      message_wait_finished_seconds: 3,
      message_wait_trailing_seconds: 20,
      message_wait_long_text_words: 10,
    });
  });

  it("shows and saves the wait cap in Conversations, with its hint", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const cap = await screen.findByLabelText("Wait cap");
    expect(cap).toHaveValue(20);
    expect(
      screen.getByRole("region", { name: "Conversations" }),
    ).toContainElement(cap);
    expect(
      screen.getByText(
        "Most seconds Zeph waits from the first text of a Message.",
      ),
    ).toBeVisible();

    await user.clear(cap);
    await user.type(cap, "30");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      message_wait_cap_seconds: 30,
    });
  });

  it("shows why a wait cap shorter than a wait was refused", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/settings",
        "The Wait cap must be at least the longest wait (12 seconds).",
      ),
    );
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const cap = await screen.findByLabelText("Wait cap");

    await user.clear(cap);
    await user.type(cap, "5");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(
      await screen.findByText(
        "The Wait cap must be at least the longest wait (12 seconds).",
      ),
    ).toBeVisible();
  });

  it("shows the trailing words with commas and saves them as a list", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const words = await screen.findByLabelText(/Trailing words/);
    expect(words).toHaveValue("and, so, ok so");
    expect(
      screen.getByRole("region", { name: "Conversations" }),
    ).toContainElement(words);
    expect(
      screen.getByText("Words that make a text trail off when they end it."),
    ).toBeVisible();

    await user.clear(words);
    await user.type(words, "and, hmm , lol,");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      message_wait_trailing_words: ["and", "hmm", "lol"],
    });
  });

  it("shows and saves the ready bars and the ruled-out topics under Patterns", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const points = await screen.findByLabelText("Score to be ready");
    const topics = screen.getByLabelText(/Ruled-out topics/);
    const patterns = screen.getByRole("region", { name: "Patterns" });
    expect(points).toHaveValue(300);
    expect(topics).toHaveValue("abuse, self-harm or suicide");
    expect(patterns).toContainElement(points);
    expect(patterns).toContainElement(topics);
    expect(screen.getByLabelText("Situations to be ready")).toHaveValue(3);
    expect(screen.getByLabelText("Conversations to be ready")).toHaveValue(2);
    expect(
      screen.getByLabelText("Evidence against must stay under"),
    ).toHaveValue(100);
    expect(
      screen.getByLabelText("Days no Pattern is ready after a Safeguard Event"),
    ).toHaveValue(14);
    expect(
      screen.getByLabelText("Day Summaries read for exclusions"),
    ).toHaveValue(7);
    expect(screen.getByText("The lowest score to be shared.")).toBeVisible();

    await user.clear(points);
    await user.type(points, "350");
    await user.clear(topics);
    await user.type(topics, "abuse, money");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      pattern_ready_points: 350,
      pattern_ruled_out_topics: ["abuse", "money"],
    });
  });

  it("won't save an empty trailing words list", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const words = await screen.findByLabelText(/Trailing words/);

    await user.clear(words);
    await user.type(words, " , ");

    expect(
      screen.getByRole("button", { name: "Save settings" }),
    ).toBeDisabled();
  });

  it("shows and saves the Recent Messages in its Conversations section", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const hours = await screen.findByLabelText("Recent messages");
    const cap = screen.getByLabelText("Recent messages cap");
    expect(hours).toHaveValue(24);
    expect(cap).toHaveValue(400);
    expect(
      screen.getByText(
        "Hours of messages, across Conversations, that every reply sees.",
      ),
    ).toBeVisible();
    const conversations = screen.getByRole("region", { name: "Conversations" });
    expect(conversations).toContainElement(hours);
    expect(conversations).toContainElement(cap);

    await user.clear(hours);
    await user.type(hours, "12");
    await user.clear(cap);
    await user.type(cap, "300");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      recent_messages_hours: 12,
      recent_messages_cap: 300,
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
    expect(
      screen.queryByRole("switch", { name: /web search/i }),
    ).not.toBeInTheDocument();
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
    const line = await screen.findByLabelText(/“Memory off” line in chat/);

    await user.type(line, " Extra.");
    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(line).toHaveValue("Nothing is deleted.");
  });

  it("says so when saving fails", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);

    await user.type(
      await screen.findByLabelText(/“Memory off” line in chat/),
      " Extra.",
    );
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t save. The platform keeps running on the last saved values.",
    );
    expect(screen.getByLabelText(/“Memory off” line in chat/)).toHaveValue(
      "Nothing is deleted. Extra.",
    );
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

  it("shows and saves the memory-off line and the data deleted reply", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const line = await screen.findByLabelText(/“Memory off” line in chat/);
    const deleted = screen.getByLabelText(/“Data deleted” reply/);
    expect(line).toHaveValue("Nothing is deleted.");
    expect(deleted).toHaveValue("Done, all deleted.");

    await user.clear(line);
    await user.type(line, "Nothing was deleted.");
    await user.clear(deleted);
    await user.type(deleted, "All gone.");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      memory_off_chat_line: "Nothing was deleted.",
      data_deleted_reply: "All gone.",
    });
  });

  it("shows and saves the Photo Viewing off note", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PlatformSettingsForm />);
    const note = await screen.findByLabelText(/Photo Viewing off” note/);
    expect(note).toHaveValue("Say you didn't look at the photo.");

    await user.clear(note);
    await user.type(note, "You didn't look.");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      photo_viewing_off_note: "You didn't look.",
    });
  });
});
