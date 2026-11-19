import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardHome } from "@/components/DashboardHome";
import type { ApiClient, Home, HomeCheckIns } from "@/lib/api-client";
import type { Copy } from "@/lib/copy";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getHome: vi.fn<ApiClient["getHome"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function checkInsWith(overrides: Partial<HomeCheckIns> = {}): HomeCheckIns {
  return {
    enabled: true,
    available: true,
    frequency: "few_times_a_week",
    quiet_hours_start: "22:00:00",
    quiet_hours_end: "07:30:00",
    paused: false,
    paused_until: null,
    pause_changed_in_chat_at: null,
    last_sent: {
      id: "c1",
      outcome: "sent",
      kind: "A casual hello",
      decided_at: "2026-11-09T10:00:00Z",
      status: "replied",
      skipped_for_daily_limit: false,
    },
    ...overrides,
  };
}

function homeWith(overrides: Partial<Home> = {}): Home {
  return {
    name: "Maya",
    time_zone: "Asia/Singapore",
    telegram_connection: {
      telegram_username: "maya_l",
      connected_at: "2026-11-01T09:00:00Z",
    },
    telegram_chat_url: "https://t.me/zeph_bot",
    last_conversation_at: "2026-11-11T11:48:00Z",
    check_ins: checkInsWith(),
    user_memory_enabled: true,
    user_memory_available: true,
    goals: [
      {
        id: "g1",
        content: "Be present at dinner",
        source: "conversation",
        created_at: "2026-10-02T09:00:00Z",
        updated_at: "2026-10-02T09:00:00Z",
      },
    ],
    recently_remembered: [
      {
        id: "m1",
        content: "Sister Jo is moving abroad",
        source: "conversation",
        created_at: "2026-11-06T09:00:00Z",
        updated_at: "2026-11-06T09:00:00Z",
        category: "Relationships",
      },
    ],
    ...overrides,
  };
}

/**
 * Says what words on Home did not come from marked Copy, besides the
 * User's own data.
 *
 * @param container - The rendered page.
 * @param allowed - Words that are allowed not to be Copy.
 * @returns Each piece of text not from Copy or the allowed words.
 */
function homeWordsNotFromCopy(
  container: HTMLElement,
  allowed: string[],
): string[] {
  return wordsNotFromCopy(container)
    .map((text) =>
      allowed
        .reduce((rest, word) => rest.replaceAll(word, ""), text)
        .replace(/\s/g, ""),
    )
    .filter((text) => text !== "");
}

/** The User's data the Home fixture shows, and the "To build" tag. */
const notCopy = [
  "Be present at dinner",
  "Sister Jo is moving abroad",
  "Relationships",
  "To build",
];

function section(name: string): HTMLElement {
  return screen.getByRole("region", { name });
}

describe("DashboardHome", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-11T12:00:00Z"));
    apiClient.getHome.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("greets the User, says when they last talked, and shows who Telegram is connected as", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    expect(
      await screen.findByRole("heading", { name: "Good evening, Maya." }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("You last talked with Zeph today."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Talk to Zeph" })).toHaveAttribute(
      "href",
      "https://t.me/zeph_bot",
    );
    const telegram = section("Telegram");
    expect(
      within(telegram).getByText("Connected as @maya_l"),
    ).toBeInTheDocument();
    expect(
      within(telegram).getByRole("link", { name: "Manage connection" }),
    ).toHaveAttribute("href", "/connect-telegram");
    expect(
      screen.queryByRole("link", { name: "Connect Telegram" }),
    ).not.toBeInTheDocument();
  });

  it("leads to Connect Telegram when Telegram isn't connected", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ telegram_connection: null, last_conversation_at: null }),
    );

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    expect(
      await screen.findByText("Zeph can’t reach you yet."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Connect Telegram" }),
    ).toHaveAttribute("href", "/connect-telegram");
    expect(
      screen.getByText("You haven't talked with Zeph yet."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Telegram" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Talk to Zeph" })).toBeNull();
  });

  it("shows Check-ins on, with quiet hours and the last Check-in sent", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("On")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("A few times a week"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText("10:00 PM to 7:30 AM"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Monday · you replied"),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText(/next/i)).toBeNull();
    expect(
      within(checkIns).getByRole("link", { name: "Change check-in settings" }),
    ).toHaveAttribute("href", "/check-ins");
  });

  it("shows Check-ins paused until a day", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({
        check_ins: checkInsWith({
          paused: true,
          paused_until: "2026-11-18T03:00:00Z",
          pause_changed_in_chat_at: "2026-11-11T03:00:00Z",
        }),
      }),
    );

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getAllByText("Paused")).toHaveLength(2);
    expect(
      within(checkIns).getByText("until Wednesday, 18 November"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Changed in chat · 11 Nov"),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText("How often")).toBeNull();
    expect(
      within(checkIns).getByText("Monday · you replied"),
    ).toBeInTheDocument();
  });

  it("shows Check-ins off without a last Check-in", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ check_ins: checkInsWith({ enabled: false }) }),
    );

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("Off")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Zeph only replies when you message"),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText("Last check-in")).toBeNull();
  });

  it("shows Check-ins as not available when an Admin has them off", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ check_ins: checkInsWith({ available: false }) }),
    );

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("Off")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Not available on your account"),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText("Last check-in")).toBeNull();
  });

  it("shows Goals and recent Memory Items, each linking to Memories", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const goals = section("What you're working toward");
    expect(within(goals).getByText("Be present at dinner")).toBeInTheDocument();
    expect(within(goals).getByText("Remembered 2 Oct")).toBeInTheDocument();
    expect(
      within(goals).getByRole("link", { name: "See in Memories" }),
    ).toHaveAttribute("href", "/memories");
    const recent = section("Recently remembered");
    expect(
      within(recent).getByText("Sister Jo is moving abroad"),
    ).toBeInTheDocument();
    expect(within(recent).getByText("Relationships")).toBeInTheDocument();
    expect(
      within(recent).getByRole("link", { name: "Review all" }),
    ).toHaveAttribute("href", "/memories");
  });

  it("shows the Plan card as to build, with the design's placeholders", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const plan = section("Plan To build");
    expect(within(plan).getByText("[PLAN NAME]")).toBeInTheDocument();
    expect(
      within(plan).getByRole("link", { name: "Manage plan" }),
    ).toHaveAttribute("href", "/plan");
  });

  it("says when nothing is remembered yet", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ goals: [], recently_remembered: [] }),
    );

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    expect(
      within(section("What you're working toward")).getByText(
        "Nothing here yet",
      ),
    ).toBeInTheDocument();
    expect(
      within(section("Recently remembered")).getByText("No memories yet"),
    ).toBeInTheDocument();
  });

  it("keeps showing Goals and Recently remembered with the note while memory is off", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ user_memory_enabled: false }),
    );

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const note = screen.getByRole("status");
    expect(note).toHaveTextContent(
      `Memory is paused. ${seedCopy()["shared.memory_off.paused_body"]}`,
    );
    expect(within(note).getByText("Memory is paused.")).toHaveClass(
      "text-text",
    );
    expect(screen.queryByText("Memory is on.")).toBeNull();
    expect(
      within(section("What you're working toward")).getByText(
        "Be present at dinner",
      ),
    ).toBeInTheDocument();
    expect(
      within(section("Recently remembered")).getByText(
        "Sister Jo is moving abroad",
      ),
    ).toBeInTheDocument();
  });

  it("says Memory is on while it is", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    expect(screen.getByText("Memory is on.")).toBeInTheDocument();
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("says Memory isn't available while an Admin has it off, even with the User's switch on", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ user_memory_available: false }),
    );
    const copy = {
      ...seedCopy(),
      "shared.memory_off.not_available_title": "Edited: not on your plan.",
      "shared.memory_off.not_available_body": "Edited: nothing is deleted.",
    };

    renderWithQueries(<DashboardHome copy={copy} />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    expect(screen.getByRole("status")).toHaveTextContent(
      "Edited: not on your plan. Edited: nothing is deleted.",
    );
    expect(screen.getByText("Edited: not on your plan.")).toHaveClass(
      "text-text",
    );
    expect(screen.queryByText("Memory is paused.")).toBeNull();
  });

  it("shows the AI notice and that Zeph doesn't count streaks", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    expect(
      await screen.findByText(
        "Zeph is an AI companion. It isn't a mental-health service and can't help in an emergency.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Zeph doesn't count streaks or time spent/),
    ).toBeInTheDocument();
  });

  it("offers Try again when home could not be loaded", async () => {
    apiClient.getHome.mockRejectedValueOnce(new Error("down"));
    apiClient.getHome.mockResolvedValueOnce(homeWith());

    renderWithQueries(<DashboardHome copy={seedCopy()} />);

    expect(
      await screen.findByText("We couldn’t load your Dashboard"),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByRole("heading", { name: "Good evening, Maya." }),
    ).toBeInTheDocument();
  });

  it("words the page from an Admin's Copy, with live values filled in", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());
    const copy: Copy = {
      ...seedCopy(),
      "home.hero.greeting_evening": "Hello again, {name}.",
      "home.telegram.connected_as": "Linked to @{username}",
      "home.goals.remembered": "Noted on {day}",
    };

    renderWithQueries(<DashboardHome copy={copy} />);

    expect(
      await screen.findByRole("heading", { name: "Hello again, Maya." }),
    ).toBeInTheDocument();
    expect(screen.getByText("Linked to @maya_l")).toBeInTheDocument();
    expect(screen.getByText("Noted on 2 Oct")).toBeInTheDocument();
  });

  it.each([
    ["Telegram connected with Check-ins on", homeWith()],
    [
      "Telegram not connected, nothing remembered, Check-ins paused",
      homeWith({
        telegram_connection: null,
        last_conversation_at: null,
        goals: [],
        recently_remembered: [],
        check_ins: checkInsWith({
          paused: true,
          paused_until: "2026-11-18T03:00:00Z",
          pause_changed_in_chat_at: "2026-11-11T03:00:00Z",
          last_sent: null,
        }),
      }),
    ],
    [
      "Check-ins off",
      homeWith({ check_ins: checkInsWith({ enabled: false }) }),
    ],
    ["Memory paused", homeWith({ user_memory_enabled: false })],
    ["Memory not available", homeWith({ user_memory_available: false })],
    [
      "Check-ins not available",
      homeWith({
        telegram_connection: {
          telegram_username: null,
          connected_at: "2026-11-01T09:00:00Z",
        },
        check_ins: checkInsWith({ available: false }),
      }),
    ],
  ])("shows only Copy text with %s", async (_state, home) => {
    apiClient.getHome.mockResolvedValue(home);

    const { container } = renderWithQueries(
      <DashboardHome copy={markedCopy()} />,
    );

    await screen.findByRole("heading", {
      name: "⟦home.hero.greeting_evening⟧",
    });
    expect(homeWordsNotFromCopy(container, notCopy)).toEqual([]);
  });

  it("shows only Copy text while loading and when Home can't load", async () => {
    apiClient.getHome.mockRejectedValue(new Error("down"));

    const { container } = renderWithQueries(
      <DashboardHome copy={markedCopy()} />,
    );

    expect(
      screen.getByRole("status", { name: "⟦home.loading⟧" }),
    ).toBeInTheDocument();
    expect(homeWordsNotFromCopy(container, [])).toEqual([]);
    expect(
      await screen.findByText("⟦home.load_failed.title⟧"),
    ).toBeInTheDocument();
    expect(homeWordsNotFromCopy(container, [])).toEqual([]);
  });
});
