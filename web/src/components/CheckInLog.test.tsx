import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInLog } from "@/components/CheckInLog";
import type { ApiClient, CheckInLogEntry } from "@/lib/api-client";

const apiClient = {
  listCheckInLog: vi.fn<ApiClient["listCheckInLog"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

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

describe("CheckInLog", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listCheckInLog.mockResolvedValue(entries);
  });

  it("lists sends, skips with reasons and ignore-rule pauses, never message text", async () => {
    render(<CheckInLog />);

    expect(await screen.findByText("No message content")).toBeInTheDocument();
    expect(apiClient.listCheckInLog).toHaveBeenCalledWith(7);
    expect(rowTexts()).toEqual([
      ["Maya Lin", "Skipped", "—", "Asked for space this week", "—"],
      ["Ren Okafor", "Sent", "A present-moment pause", "—", "Replied"],
      [
        "aiko@example.com",
        "Paused",
        "—",
        "Ignore threshold reached — asked once about fewer",
        "Waiting",
      ],
    ]);
  });

  it("shows the totals for the period", async () => {
    render(<CheckInLog />);

    await screen.findByRole("table");
    const terms = screen.getAllByRole("term").map((term) => term.textContent);
    const values = screen
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
    render(<CheckInLog />);
    await screen.findByRole("table");

    await user.click(screen.getByRole("button", { name: "Skipped" }));
    expect(rowTexts().map((row) => row[0])).toEqual(["Maya Lin"]);

    await user.click(screen.getByRole("button", { name: "All" }));
    await user.type(screen.getByPlaceholderText("Filter by user"), "ren");
    expect(rowTexts().map((row) => row[0])).toEqual(["Ren Okafor"]);

    await user.selectOptions(screen.getByLabelText("Period"), "30");
    expect(apiClient.listCheckInLog).toHaveBeenLastCalledWith(30);
  });

  it("says when there are no decisions yet", async () => {
    apiClient.listCheckInLog.mockResolvedValue([]);
    render(<CheckInLog />);

    expect(
      await screen.findByText("No Check-in decisions yet"),
    ).toBeInTheDocument();
  });

  it("offers Try again when the log can't load", async () => {
    apiClient.listCheckInLog.mockRejectedValue(new Error("down"));
    render(<CheckInLog />);

    expect(
      await screen.findByText("Couldn’t load the Check-in log"),
    ).toBeInTheDocument();
  });
});
