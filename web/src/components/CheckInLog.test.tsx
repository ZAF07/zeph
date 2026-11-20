import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInLog } from "@/components/CheckInLog";
import type { ApiClient, CheckInLogEntry } from "@/lib/api-client";
import { formatLoggedAt } from "@/lib/dates";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listCheckInLog: vi.fn<ApiClient["listCheckInLog"]>(),
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

/** The settings with only the Ignore Threshold, as the log reads it. */
function settingsWithIgnoreThreshold(value: number) {
  return {
    check_in_ignore_threshold: {
      label: "Ignore threshold",
      hint: "",
      value,
      updated_at: "2026-11-01T09:00:00Z",
      updated_by: null,
    },
  };
}

const entries: CheckInLogEntry[] = [
  {
    id: "c3",
    user_id: "u1",
    user_name: "Maya Lin",
    user_email: "maya@example.com",
    decided_at: "2026-11-11T10:30:00Z",
    outcome: "skipped",
    kind: null,
    skip_reason: "Asked for space this week",
    status: "skipped",
    requested_by: null,
    woven_in: false,
  },
  {
    id: "c2",
    user_id: "u2",
    user_name: "Ren Okafor",
    user_email: "ren@example.com",
    decided_at: "2026-11-11T04:05:00Z",
    outcome: "sent",
    kind: "A present-moment pause",
    skip_reason: null,
    status: "replied",
    requested_by: "Sam Admin",
    woven_in: true,
  },
  {
    id: "c1",
    user_id: "u3",
    user_name: null,
    user_email: "aiko@example.com",
    decided_at: "2026-11-08T08:20:00Z",
    outcome: "asked_about_fewer",
    kind: null,
    skip_reason: null,
    status: "sent",
    requested_by: null,
    woven_in: false,
  },
];

function rowTexts() {
  const rows = within(screen.getByRole("table")).getAllByRole("row");
  return rows.slice(1).map((row) =>
    within(row)
      .getAllByRole("cell")
      .slice(1)
      .map((cell) => cell.textContent),
  );
}

function table() {
  return within(screen.getByRole("table"));
}

describe("CheckInLog", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listCheckInLog.mockResolvedValue(entries);
    apiClient.getAdminSettings.mockResolvedValue(
      settingsWithIgnoreThreshold(3),
    );
  });

  it("lists sends, woven in or not, skips with reasons and ignore-rule pauses, never message text", async () => {
    renderWithQueries(<CheckInLog />);

    expect(await screen.findByText("No message content")).toBeInTheDocument();
    expect(apiClient.listCheckInLog).toHaveBeenCalledWith(7);
    expect(rowTexts()).toEqual([
      ["Maya Lin", "Skipped", "—", "Asked for space this week", "—"],
      [
        "Ren Okafor",
        "SentAsked for by Sam AdminWoven in",
        "A present-moment pause",
        "—",
        "Replied",
      ],
      [
        "aiko@example.com",
        "Paused",
        "—",
        "Three in a row went unanswered",
        "Waiting",
      ],
    ]);
  });

  it("shows when each decision was made, with the weekday and a 12-hour time", async () => {
    renderWithQueries(<CheckInLog />);

    await screen.findByRole("table");
    const firstCells = table()
      .getAllByRole("row")
      .slice(1)
      .map((row) => within(row).getAllByRole("cell")[0].textContent);
    expect(firstCells).toEqual(
      entries.map((entry) => formatLoggedAt(entry.decided_at)),
    );
  });

  it("names the Ignore Threshold set by the Admins on paused rows", async () => {
    apiClient.getAdminSettings.mockResolvedValue(
      settingsWithIgnoreThreshold(5),
    );
    renderWithQueries(<CheckInLog />);

    await screen.findByRole("table");
    expect(
      table().getByText("Five in a row went unanswered"),
    ).toBeInTheDocument();
  });

  it("keeps the loading rows until the settings have loaded too", async () => {
    apiClient.getAdminSettings.mockReturnValue(new Promise(() => {}));
    renderWithQueries(<CheckInLog />);

    expect(
      await screen.findByRole("status", { name: "Loading log" }),
    ).toBeInTheDocument();
    await waitFor(() => expect(apiClient.listCheckInLog).toHaveBeenCalled());
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("still shows the log when the settings can't load", async () => {
    apiClient.getAdminSettings.mockRejectedValue(new Error("down"));
    renderWithQueries(<CheckInLog />);

    await screen.findByRole("table");
    expect(table().getByText("Paused by ignore rule")).toBeInTheDocument();
    expect(table().queryByText(/in a row went unanswered/)).toBeNull();
  });

  it("says which Admin asked for a Check in Now", async () => {
    renderWithQueries(<CheckInLog />);

    await screen.findByRole("table");
    expect(table().getByText("Asked for by Sam Admin")).toBeVisible();
    expect(table().getAllByText(/Asked for by/)).toHaveLength(1);
  });

  it("shows each row as a card of label and value lines for phones", async () => {
    renderWithQueries(<CheckInLog />);

    await screen.findByRole("table");
    const mayaCard = screen
      .getAllByRole("term")
      .filter((term) => term.textContent === "User")
      .map((term) => term.nextElementSibling?.textContent);
    expect(mayaCard).toEqual(["Maya Lin", "Ren Okafor", "aiko@example.com"]);
  });

  it("shows the totals for the period", async () => {
    renderWithQueries(<CheckInLog />);

    await screen.findByRole("table");
    const totals = within(screen.getByRole("region", { name: "Totals" }));
    const terms = totals.getAllByRole("term").map((term) => term.textContent);
    const values = totals
      .getAllByRole("definition")
      .map((value) => value.textContent);
    expect(terms).toEqual([
      "Sent",
      "Skipped",
      "Replied to",
      "Paused by ignore rule",
    ]);
    expect(values).toEqual(["1", "1", "100%", "1"]);
  });

  it("filters by outcome and User, and loads a longer period", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInLog />);
    await screen.findByRole("table");

    await user.click(screen.getByRole("button", { name: "Skipped" }));
    expect(rowTexts().map((row) => row[0])).toEqual(["Maya Lin"]);

    await user.click(screen.getByRole("button", { name: "All" }));
    await user.type(screen.getByPlaceholderText("Filter by user"), "ren");
    expect(rowTexts().map((row) => row[0])).toEqual(["Ren Okafor"]);

    await user.selectOptions(screen.getByLabelText("Period"), "30");
    expect(apiClient.listCheckInLog).toHaveBeenLastCalledWith(30);
  });

  it("shows soft loading rows while the log loads", async () => {
    apiClient.listCheckInLog.mockReturnValue(new Promise(() => {}));
    renderWithQueries(<CheckInLog />);

    expect(
      await screen.findByRole("status", { name: "Loading log" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("says when the filters match nothing, in place of the table", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInLog />);
    await screen.findByRole("table");

    await user.type(screen.getByPlaceholderText("Filter by user"), "nobody");

    expect(
      screen.getByText("Nothing matches these filters."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("says when nothing is logged yet", async () => {
    apiClient.listCheckInLog.mockResolvedValue([]);
    renderWithQueries(<CheckInLog />);

    expect(await screen.findByText("No check-ins yet")).toBeInTheDocument();
    expect(
      screen.getByText("Entries appear once users turn check-ins on."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("offers Try again when the log can't load", async () => {
    apiClient.listCheckInLog
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(entries);
    const user = userEvent.setup();
    renderWithQueries(<CheckInLog />);

    const alert = await screen.findByRole("alert");
    expect(
      within(alert).getByRole("heading", {
        name: "Couldn’t load the Check-in log",
      }),
    ).toBeInTheDocument();
    expect(
      within(alert).getByText("Check your connection and try again."),
    ).toBeInTheDocument();

    await user.click(within(alert).getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("table")).toBeInTheDocument();
  });
});
