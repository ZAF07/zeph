import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInsSettings } from "@/components/CheckInsSettings";
import type { ApiClient, CheckIns } from "@/lib/api-client";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  getCheckIns: vi.fn<ApiClient["getCheckIns"]>(),
  updateCheckIns: vi.fn<ApiClient["updateCheckIns"]>(),
  pauseCheckIns: vi.fn<ApiClient["pauseCheckIns"]>(),
  resumeCheckIns: vi.fn<ApiClient["resumeCheckIns"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const maya = userWithRole("user");

function checkInsWith(overrides: Partial<CheckIns> = {}): CheckIns {
  return {
    enabled: true,
    available: true,
    frequency: "few_times_a_week",
    quiet_hours_start: "22:00:00",
    quiet_hours_end: "07:30:00",
    paused: false,
    paused_until: null,
    recent: [],
    kinds: [
      { name: "A casual hello", description: "Just checking how you are." },
      {
        name: "A present-moment pause",
        description: "A brief invitation to notice where you are.",
      },
    ],
    changed_by_admin: {},
    ...overrides,
  };
}

async function renderLoaded() {
  renderWithQueries(<CheckInsSettings copy={seedCopy()} />);
  await screen.findByRole("region", { name: "Settings" });
}

describe("CheckInsSettings", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getMe.mockResolvedValue(maya);
    apiClient.getCheckIns.mockResolvedValue(checkInsWith());
  });

  it("shows the saved frequency and quiet hours", async () => {
    await renderLoaded();

    expect(screen.getByText("Check-ins on")).toBeInTheDocument();
    expect(screen.getByRole("switch", { name: "Check-ins" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(
      screen.getByRole("button", { name: "A few times a week" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("From")).toHaveValue("22:00");
    expect(screen.getByLabelText("Until")).toHaveValue("07:30");
  });

  it("says Check-ins can be changed by telling Zeph", async () => {
    await renderLoaded();

    expect(
      screen.getByText(
        /You can also just tell Zeph "take a week off from check-ins"/,
      ),
    ).toBeInTheDocument();
  });

  it("marks settings last changed in chat with the day", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      changed_in_chat: {
        quiet_hours: "2026-11-03T02:00:00Z",
        check_in_pause: "2026-11-11T09:00:00Z",
      },
    });
    await renderLoaded();

    expect(screen.getByText("Changed in chat · 3 Nov")).toBeInTheDocument();
    expect(screen.getByText("Changed in chat · 11 Nov")).toBeInTheDocument();
    expect(screen.getAllByText(/Changed in chat/)).toHaveLength(2);
  });

  it("marks settings an Admin changed", async () => {
    apiClient.getCheckIns.mockResolvedValue(
      checkInsWith({
        changed_by_admin: {
          check_in_frequency: "2026-11-15T02:00:00Z",
          check_in_pause: "2026-11-16T02:00:00Z",
        },
      }),
    );
    await renderLoaded();

    expect(
      screen.getByText("Changed by an Admin · 15 Nov"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Changed by an Admin · 16 Nov"),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Changed by an Admin/)).toHaveLength(2);
  });

  it("drops the Admin mark once the User changes that setting", async () => {
    apiClient.getCheckIns.mockResolvedValue(
      checkInsWith({
        changed_by_admin: { check_in_frequency: "2026-11-15T02:00:00Z" },
      }),
    );
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ frequency: "weekly" }),
    );
    const user = userEvent.setup();
    await renderLoaded();
    expect(screen.getByText(/Changed by an Admin/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Weekly" }));

    expect(
      await screen.findByRole("button", { name: "Weekly" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByText(/Changed by an Admin/)).not.toBeInTheDocument();
  });

  it("drops the caption once the setting is changed on the Dashboard", async () => {
    apiClient.getMe.mockResolvedValueOnce({
      ...maya,
      changed_in_chat: { check_in_frequency: "2026-11-03T02:00:00Z" },
    });
    apiClient.getMe.mockResolvedValue(maya);
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ frequency: "weekly" }),
    );
    const user = userEvent.setup();
    await renderLoaded();
    expect(screen.getByText("Changed in chat · 3 Nov")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Weekly" }));

    expect(
      await screen.findByRole("button", { name: "Weekly" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByText(/Changed in chat/)).not.toBeInTheDocument();
  });

  it("saves a new frequency", async () => {
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ frequency: "weekly" }),
    );
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "Weekly" }));

    expect(apiClient.updateCheckIns).toHaveBeenCalledWith({
      frequency: "weekly",
    });
    expect(
      await screen.findByRole("button", { name: "Weekly" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("lets a User pick a few times a day", async () => {
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ frequency: "a_few_times_a_day" }),
    );
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "A few times a day" }));

    expect(apiClient.updateCheckIns).toHaveBeenCalledWith({
      frequency: "a_few_times_a_day",
    });
    expect(
      await screen.findByRole("button", { name: "A few times a day" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("saves new quiet hours, and leaves the time zone to Account", async () => {
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ quiet_hours_end: "08:15:00" }),
    );
    await renderLoaded();

    fireEvent.change(screen.getByLabelText("Until"), {
      target: { value: "08:15" },
    });
    await vi.waitFor(() =>
      expect(apiClient.updateCheckIns).toHaveBeenCalledWith({
        quiet_hours_end: "08:15",
      }),
    );
    expect(await screen.findByDisplayValue("08:15")).toBeInTheDocument();
    expect(screen.queryByLabelText("Time zone")).not.toBeInTheDocument();
  });

  it("turns Check-ins off and says Zeph will only reply", async () => {
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ enabled: false }),
    );
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("switch", { name: "Check-ins" }));

    expect(apiClient.updateCheckIns).toHaveBeenCalledWith({ enabled: false });
    expect(
      await screen.findByText("Zeph only replies when you message it."),
    ).toBeInTheDocument();
    expect(screen.getByText("Check-ins are off")).toBeInTheDocument();
    expect(screen.getByText("Check-ins off")).toBeInTheDocument();
  });

  it("shows Not available on your account with the switch disabled", async () => {
    apiClient.getCheckIns.mockResolvedValue(checkInsWith({ available: false }));
    const user = userEvent.setup();
    await renderLoaded();

    const checkInsSwitch = screen.getByRole("switch", { name: "Check-ins" });
    expect(checkInsSwitch).toBeDisabled();
    expect(checkInsSwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Not available on your account")).toBeVisible();
    expect(
      screen.getByText("Check-ins aren’t available on your account"),
    ).toBeVisible();
    expect(
      screen.getByText("Zeph won’t message you first. Your settings are kept."),
    ).toBeVisible();
    await user.click(checkInsSwitch);
    expect(apiClient.updateCheckIns).not.toHaveBeenCalled();
  });

  it("pauses for a week, says until when, and can resume", async () => {
    apiClient.pauseCheckIns.mockResolvedValue(
      checkInsWith({ paused: true, paused_until: "2026-11-18T09:00:00Z" }),
    );
    apiClient.resumeCheckIns.mockResolvedValue(checkInsWith());
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "For a week" }));

    expect(apiClient.pauseCheckIns).toHaveBeenCalledWith("week");
    expect(
      await screen.findByText("Check-ins are paused until 18 Nov"),
    ).toBeInTheDocument();
    expect(screen.getByText("Paused")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "A few times a week" }),
    ).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "Resume now" }));

    expect(apiClient.resumeCheckIns).toHaveBeenCalled();
    expect(await screen.findByText("Check-ins on")).toBeInTheDocument();
  });

  it("pauses until the User resumes", async () => {
    apiClient.pauseCheckIns.mockResolvedValue(
      checkInsWith({ paused: true, paused_until: null }),
    );
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "Until I resume" }));

    expect(apiClient.pauseCheckIns).toHaveBeenCalledWith("until_resumed");
    expect(
      await screen.findByText("Check-ins are paused until you resume"),
    ).toBeInTheDocument();
  });

  it("lists recent Check-ins with whether the User replied, and no next time", async () => {
    apiClient.getCheckIns.mockResolvedValue(
      checkInsWith({
        recent: [
          {
            id: "check-in-6",
            outcome: "skipped",
            kind: null,
            decided_at: "2026-11-13T10:42:00Z",
            status: "skipped",
            skipped_for_daily_limit: true,
          },
          {
            id: "check-in-5",
            outcome: "asked_about_fewer",
            kind: null,
            decided_at: "2026-11-12T10:42:00Z",
            status: "sent",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-4",
            outcome: "sent",
            kind: "A casual hello",
            decided_at: "2026-11-11T10:42:00Z",
            status: "no_reply",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-3",
            outcome: "skipped",
            kind: null,
            decided_at: "2026-11-10T10:42:00Z",
            status: "skipped",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-2",
            outcome: "sent",
            kind: "A casual hello",
            decided_at: "2026-11-09T10:42:00Z",
            status: "replied",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-1",
            outcome: "sent",
            kind: null,
            decided_at: "2026-11-05T04:15:00Z",
            status: "no_reply",
            skipped_for_daily_limit: false,
          },
        ],
      }),
    );
    await renderLoaded();

    const items = within(
      screen.getByRole("region", { name: "Recent check-ins" }),
    ).getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual([
      "Skipped — you’d reached today’s message limitFriday 13 NovSkipped",
      "Asked if you’d like fewerThursday 12 NovSent",
      "A casual helloWednesday 11 NovNo reply",
      "Zeph gave you spaceTuesday 10 NovSkipped",
      "A casual helloMonday 9 NovReplied",
      "A check-inThursday 5 NovNo reply",
    ]);
    expect(document.body.textContent).not.toMatch(/next check-in/i);
  });

  it("lists what a check-in can be, read-only, and explains the ignore rule", async () => {
    await renderLoaded();

    const kinds = within(
      screen.getByRole("region", { name: "What a check-in can be" }),
    ).getAllByRole("listitem");
    expect(kinds.map((kind) => kind.textContent)).toEqual([
      "A casual helloJust checking how you are.",
      "A present-moment pauseA brief invitation to notice where you are.",
    ]);
    expect(
      within(
        screen.getByRole("region", { name: "What a check-in can be" }),
      ).queryByRole("button"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "If a few go unanswered, Zeph will pause and ask once if you'd like fewer.",
      ),
    ).toBeInTheDocument();
  });

  it("says there are no Check-ins yet", async () => {
    await renderLoaded();

    expect(screen.getByText("No check-ins yet")).toBeInTheDocument();
  });

  it("says when a change could not be saved", async () => {
    apiClient.updateCheckIns.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "Most days" }));

    expect(
      await screen.findByText(
        "Couldn’t save your check-in settings. They are as you left them. Try again.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "A few times a week" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("shows an error with Try again when loading fails", async () => {
    apiClient.getCheckIns.mockRejectedValueOnce(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<CheckInsSettings copy={seedCopy()} />);

    expect(
      await screen.findByText("We couldn’t load your Check-in settings"),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("region", { name: "Settings" }),
    ).toBeInTheDocument();
  });

  describe("reads every word from Copy", () => {
    const changedAt = "2026-11-03T02:00:00Z";

    /**
     * Says what words on the page did not come from Copy, leaving out the
     * days of recent Check-ins, like "Friday 13 Nov", which are values.
     *
     * @param container - The rendered page.
     * @returns Each piece of text not from Copy or a day.
     */
    function wordsNotFromCopyOrDays(container: HTMLElement): string[] {
      const words = container.cloneNode(true) as HTMLElement;
      words.querySelectorAll("div").forEach((line) => {
        if (
          /^[A-Z][a-z]+ \d{1,2} [A-Z][a-z]{2}$/.test(line.textContent ?? "")
        ) {
          line.remove();
        }
      });
      return wordsNotFromCopy(words);
    }

    function markedCheckIns(overrides: Partial<CheckIns> = {}): CheckIns {
      return checkInsWith({
        kinds: [{ name: "⟦data⟧", description: "⟦data⟧" }],
        recent: [
          {
            id: "check-in-4",
            outcome: "skipped",
            kind: null,
            decided_at: "2026-11-13T10:42:00Z",
            status: "skipped",
            skipped_for_daily_limit: true,
          },
          {
            id: "check-in-3",
            outcome: "asked_about_fewer",
            kind: null,
            decided_at: "2026-11-12T10:42:00Z",
            status: "sent",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-2",
            outcome: "sent",
            kind: "⟦data⟧",
            decided_at: "2026-11-11T10:42:00Z",
            status: "replied",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-1",
            outcome: "skipped",
            kind: null,
            decided_at: "2026-11-10T10:42:00Z",
            status: "no_reply",
            skipped_for_daily_limit: false,
          },
          {
            id: "check-in-0",
            outcome: "sent",
            kind: null,
            decided_at: "2026-11-09T10:42:00Z",
            status: "no_reply",
            skipped_for_daily_limit: false,
          },
        ],
        changed_by_admin: { quiet_hours: changedAt },
        ...overrides,
      });
    }

    async function renderMarked() {
      const view = renderWithQueries(<CheckInsSettings copy={markedCopy()} />);
      await screen.findByRole("region", {
        name: "⟦check_ins.settings.label⟧",
      });
      return view;
    }

    beforeEach(() => {
      apiClient.getMe.mockResolvedValue({
        ...maya,
        changed_in_chat: { check_in_frequency: changedAt },
      });
    });

    it("with Check-ins on, settings changed and recent Check-ins", async () => {
      apiClient.getCheckIns.mockResolvedValue(markedCheckIns());
      const { container } = await renderMarked();

      expect(screen.getByText("⟦check_ins.switch.on⟧")).toBeInTheDocument();
      expect(
        screen.getByText("⟦check_ins.changed_in_chat⟧"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("⟦check_ins.changed_by_admin⟧"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("⟦check_ins.recent.no_kind⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("while paused, and with nothing sent yet", async () => {
      apiClient.getCheckIns.mockResolvedValue(
        markedCheckIns({ paused: true, paused_until: null, recent: [] }),
      );
      const { container } = await renderMarked();

      expect(
        screen.getByText("⟦check_ins.paused.title_until_resume⟧"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("⟦check_ins.recent.empty_title⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("while paused until a day", async () => {
      apiClient.getCheckIns.mockResolvedValue(
        markedCheckIns({ paused: true, paused_until: changedAt }),
      );
      const { container } = await renderMarked();

      expect(
        screen.getByText("⟦check_ins.paused.title_until_day⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("while off", async () => {
      apiClient.getCheckIns.mockResolvedValue(
        markedCheckIns({ enabled: false }),
      );
      const { container } = await renderMarked();

      expect(screen.getByText("⟦check_ins.off.title⟧")).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("when an Admin has Check-ins off", async () => {
      apiClient.getCheckIns.mockResolvedValue(
        markedCheckIns({ available: false }),
      );
      const { container } = await renderMarked();

      expect(
        screen.getByText("⟦check_ins.not_available.title⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("when a change couldn't be saved", async () => {
      apiClient.getCheckIns.mockResolvedValue(markedCheckIns());
      apiClient.updateCheckIns.mockRejectedValue(new Error("down"));
      const user = userEvent.setup();
      const { container } = await renderMarked();

      await user.click(
        screen.getByRole("button", {
          name: "⟦onboarding.check_ins.frequency_most_days⟧",
        }),
      );

      expect(
        await screen.findByText("⟦check_ins.save_failed⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("while loading, and when loading fails", async () => {
      apiClient.getCheckIns.mockRejectedValue(new Error("down"));
      const { container } = renderWithQueries(
        <CheckInsSettings copy={markedCopy()} />,
      );

      expect(
        screen.getByRole("status", { name: "⟦check_ins.loading⟧" }),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
      expect(
        await screen.findByText("⟦check_ins.load_failed.title⟧"),
      ).toBeInTheDocument();
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });
  });
});
