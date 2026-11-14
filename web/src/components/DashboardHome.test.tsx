import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardHome } from "@/components/DashboardHome";
import type { ApiClient, Home, HomeCheckIns } from "@/lib/api-client";

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
    memory_note: "",
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
    ai_notice: "Zeph is an AI, not a therapist or crisis service.",
    ...overrides,
  };
}

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

  it("greets the User and shows who Telegram is connected as", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    render(<DashboardHome />);

    expect(
      await screen.findByRole("heading", { name: "Good evening, Maya." }),
    ).toBeInTheDocument();
    expect(screen.getByText("Wednesday, 11 November")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Talk to Zeph" })).toHaveAttribute(
      "href",
      "https://t.me/zeph_bot",
    );
    const telegram = section("Telegram");
    expect(
      within(telegram).getByText("Connected as @maya_l"),
    ).toBeInTheDocument();
    expect(
      within(telegram).getByText("Last Conversation today at 7:48 pm."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Connect Telegram" }),
    ).not.toBeInTheDocument();
  });

  it("leads to Connect Telegram when Telegram isn't connected", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ telegram_connection: null, last_conversation_at: null }),
    );

    render(<DashboardHome />);

    const banner = await screen.findByRole("region", {
      name: "Zeph can’t reach you yet.",
    });
    expect(
      within(banner).getByRole("link", { name: "Connect Telegram" }),
    ).toHaveAttribute("href", "/connect-telegram");
    expect(screen.queryByRole("region", { name: "Telegram" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Talk to Zeph" })).toBeNull();
  });

  it("shows Check-ins on, with quiet hours and the last Check-in sent", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("On")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("A few times a week, at most"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Never between 10:00 pm and 7:30 am"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText(
        "Last Check-in: a casual hello, Mon 9 Nov · you replied",
      ),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText(/next/i)).toBeNull();
    expect(
      within(checkIns).getByRole("link", { name: "Check-in settings" }),
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

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("Paused")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("until Wednesday, 18 November"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Changed in chat · 11 Nov"),
    ).toBeInTheDocument();
    expect(
      within(checkIns).getByText(/^Last Check-in: a casual hello/),
    ).toBeInTheDocument();
  });

  it("shows Check-ins off without a last Check-in", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ check_ins: checkInsWith({ enabled: false }) }),
    );

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("Off")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Zeph only replies when you message"),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText(/^Last Check-in/)).toBeNull();
  });

  it("shows Check-ins as not available when an Admin has them off", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ check_ins: checkInsWith({ available: false }) }),
    );

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const checkIns = section("Check-ins");
    expect(within(checkIns).getByText("Off")).toBeInTheDocument();
    expect(
      within(checkIns).getByText("Not available on your account"),
    ).toBeInTheDocument();
    expect(within(checkIns).queryByText(/A casual hello/)).toBeNull();
  });

  it("shows Goals and recent Memory Items, each linking to Memories", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const goals = section("What you’re working toward");
    expect(within(goals).getByText("Be present at dinner")).toBeInTheDocument();
    expect(
      within(goals).getByText("From a conversation · 2 Oct"),
    ).toBeInTheDocument();
    expect(
      within(goals).getByRole("link", { name: "See in Memories" }),
    ).toHaveAttribute("href", "/memories");
    const recent = section("Recently remembered");
    expect(
      within(recent).getByText("Sister Jo is moving abroad"),
    ).toBeInTheDocument();
    expect(
      within(recent).getByText("Relationships · 6 Nov"),
    ).toBeInTheDocument();
    expect(
      within(recent).getByRole("link", { name: "Review all" }),
    ).toHaveAttribute("href", "/memories");
  });

  it("says when nothing is remembered yet", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({ goals: [], recently_remembered: [] }),
    );

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    expect(
      within(section("What you’re working toward")).getByText(
        "Nothing here yet",
      ),
    ).toBeInTheDocument();
    expect(
      within(section("Recently remembered")).getByText(
        "No memories yet. They’ll appear after your first Conversation.",
      ),
    ).toBeInTheDocument();
  });

  it("keeps showing Goals and Recently remembered with the note while memory is off", async () => {
    apiClient.getHome.mockResolvedValue(
      homeWith({
        user_memory_enabled: false,
        memory_note:
          "**Memory is paused.** Zeph won’t learn anything new, but still uses what it already knows about you.",
      }),
    );

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    const note = screen.getByRole("status");
    expect(note).toHaveTextContent(
      "Memory is paused. Zeph won’t learn anything new, but still uses what it already knows about you.",
    );
    expect(within(note).getByText("Memory is paused.").tagName).toBe("STRONG");
    expect(
      within(section("What you’re working toward")).getByText(
        "Be present at dinner",
      ),
    ).toBeInTheDocument();
    expect(
      within(section("Recently remembered")).getByText(
        "Sister Jo is moving abroad",
      ),
    ).toBeInTheDocument();
  });

  it("shows no memory note while memory is on", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    render(<DashboardHome />);

    await screen.findByRole("heading", { name: "Good evening, Maya." });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("shows the AI notice and that Zeph doesn't count streaks", async () => {
    apiClient.getHome.mockResolvedValue(homeWith());

    render(<DashboardHome />);

    expect(
      await screen.findByText(
        "Zeph is an AI, not a therapist or crisis service.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Zeph doesn’t count streaks or time spent/),
    ).toBeInTheDocument();
  });

  it("offers Try again when home could not be loaded", async () => {
    apiClient.getHome.mockRejectedValueOnce(new Error("down"));
    apiClient.getHome.mockResolvedValueOnce(homeWith());

    render(<DashboardHome />);

    expect(
      await screen.findByText("We couldn’t load your Dashboard"),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByRole("heading", { name: "Good evening, Maya." }),
    ).toBeInTheDocument();
  });
});
