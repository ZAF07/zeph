import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInsSettings } from "@/components/CheckInsSettings";
import type { ApiClient, CheckIns } from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
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
    ...overrides,
  };
}

async function renderLoaded() {
  render(<CheckInsSettings />);
  await screen.findByRole("heading", { name: "Settings" });
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
    expect(screen.getByLabelText("Time zone")).toHaveValue("Asia/Singapore");
  });

  it("saves a new frequency", async () => {
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ frequency: "weekly" }),
    );
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "Once a week" }));

    expect(apiClient.updateCheckIns).toHaveBeenCalledWith({
      frequency: "weekly",
    });
    expect(
      await screen.findByRole("button", { name: "Once a week" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("saves new quiet hours and a new time zone", async () => {
    apiClient.updateCheckIns.mockResolvedValue(
      checkInsWith({ quiet_hours_end: "08:15:00" }),
    );
    apiClient.updatePreferences.mockResolvedValue({
      ...maya,
      time_zone: "Europe/London",
    });
    const user = userEvent.setup();
    await renderLoaded();

    fireEvent.change(screen.getByLabelText("Until"), {
      target: { value: "08:15" },
    });
    expect(apiClient.updateCheckIns).toHaveBeenCalledWith({
      quiet_hours_end: "08:15",
    });
    expect(await screen.findByDisplayValue("08:15")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Time zone"), [
      "Europe/London",
    ]);
    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      time_zone: "Europe/London",
    });
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
      await screen.findByText(
        "Check-ins are off. Zeph only replies when you message it.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Check-ins off")).toBeInTheDocument();
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
      await screen.findByText("Paused until Wednesday, 18 November."),
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
      await screen.findByText("Paused until you resume."),
    ).toBeInTheDocument();
  });

  it("lists recent Check-ins with whether the User replied, and no next time", async () => {
    apiClient.getCheckIns.mockResolvedValue(
      checkInsWith({
        recent: [
          {
            id: "check-in-5",
            outcome: "asked_about_fewer",
            kind: null,
            decided_at: "2026-11-12T10:42:00Z",
            status: "sent",
          },
          {
            id: "check-in-4",
            outcome: "sent",
            kind: "A casual hello",
            decided_at: "2026-11-11T10:42:00Z",
            status: "no_reply",
          },
          {
            id: "check-in-3",
            outcome: "skipped",
            kind: null,
            decided_at: "2026-11-10T10:42:00Z",
            status: "skipped",
          },
          {
            id: "check-in-2",
            outcome: "sent",
            kind: "A casual hello",
            decided_at: "2026-11-09T10:42:00Z",
            status: "replied",
          },
          {
            id: "check-in-1",
            outcome: "sent",
            kind: null,
            decided_at: "2026-11-05T04:15:00Z",
            status: "no_reply",
          },
        ],
      }),
    );
    await renderLoaded();

    const items = within(
      screen.getByRole("region", { name: "Recent check-ins" }),
    ).getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual([
      "Asked if you’d like fewerThu 12 Nov · 6:42 pmSent",
      "A casual helloWed 11 Nov · 6:42 pmNo reply",
      "Skipped — gave you some spaceTue 10 NovSkipped",
      "A casual helloMon 9 Nov · 6:42 pmReplied",
      "A check-inThu 5 Nov · 12:15 pmNo reply",
    ]);
    expect(document.body.textContent).not.toMatch(/next check-in/i);
  });

  it("lists what Zeph might reach out about, read-only, and explains the ignore rule", async () => {
    await renderLoaded();

    const kinds = within(
      screen.getByRole("region", { name: "What Zeph might reach out about" }),
    ).getAllByRole("listitem");
    expect(kinds.map((kind) => kind.textContent)).toEqual([
      "A casual helloJust checking how you are.",
      "A present-moment pauseA brief invitation to notice where you are.",
    ]);
    expect(
      within(
        screen.getByRole("region", { name: "What Zeph might reach out about" }),
      ).queryByRole("button"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "If a few go unanswered, Zeph will pause and ask once if you’d like fewer.",
      ),
    ).toBeInTheDocument();
  });

  it("says there are no Check-ins yet", async () => {
    await renderLoaded();

    expect(screen.getByText("No Check-ins yet")).toBeInTheDocument();
  });

  it("says when a change could not be saved", async () => {
    apiClient.updateCheckIns.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    await renderLoaded();

    await user.click(screen.getByRole("button", { name: "Most days" }));

    expect(
      await screen.findByText("We couldn’t save that. Please try again."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "A few times a week" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("shows an error with Try again when loading fails", async () => {
    apiClient.getCheckIns.mockRejectedValueOnce(new Error("down"));
    const user = userEvent.setup();
    render(<CheckInsSettings />);

    expect(
      await screen.findByText("We couldn’t load your Check-in settings"),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("heading", { name: "Settings" }),
    ).toBeInTheDocument();
  });
});
