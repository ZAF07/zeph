import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInSchedule } from "@/components/CheckInSchedule";
import type { ApiClient } from "@/lib/api-client";
import { scheduleEntry, schedulePage } from "@/test/check-in-schedule";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listCheckInSchedule: vi.fn<ApiClient["listCheckInSchedule"]>(),
  changeUserCheckIns: vi.fn<ApiClient["changeUserCheckIns"]>(),
  pauseUserCheckIns: vi.fn<ApiClient["pauseUserCheckIns"]>(),
  resumeUserCheckIns: vi.fn<ApiClient["resumeUserCheckIns"]>(),
  checkInNow: vi.fn<ApiClient["checkInNow"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function rowFor(name: string): HTMLElement {
  const row = screen.getByText(name).closest("tr");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return row;
}

describe("CheckInSchedule", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listCheckInSchedule.mockResolvedValue(
      schedulePage([
        scheduleEntry(),
        scheduleEntry({
          user_id: "sam",
          name: "Sam Lee",
          email: "sam@example.com",
          next_due_at: "2026-11-16T09:00:00Z",
          frequency: "weekly",
          paused: true,
          paused_until: "2026-11-24T02:00:00Z",
          check_ins_work: false,
          held_back: { reason: "quiet_hours", until: "2026-11-16T23:30:00Z" },
        }),
      ]),
    );
  });

  it("shows each opted-in User's Due Time, settings, Feature and held-back state", async () => {
    renderWithQueries(<CheckInSchedule />);

    await screen.findByText("Ren Okafor");
    const ren = within(rowFor("Ren Okafor"));
    expect(ren.getByText("ren@example.com")).toBeVisible();
    expect(ren.getByText("in 3 h · Tue 13:00 their time")).toBeVisible();
    expect(ren.getByText("Most days")).toBeVisible();
    expect(ren.getByText("22:00–07:30")).toBeVisible();
    expect(ren.getByText("Not paused")).toBeVisible();
    expect(ren.getByText("Works")).toBeVisible();
    expect(ren.getByText("—")).toBeVisible();

    const sam = within(rowFor("Sam Lee"));
    expect(sam.getByText("due now")).toBeVisible();
    expect(sam.getByText("Weekly")).toBeVisible();
    expect(sam.getByText("Paused until Tue 24 Nov 10:00")).toBeVisible();
    expect(sam.getByText("Feature off")).toBeVisible();
    expect(sam.getByText("Quiet Hours, until 07:30")).toBeVisible();
    expect(screen.getByText(/No message content · 2 Users/)).toBeVisible();
  });

  it("searches by name or email and starts again from the first page", async () => {
    apiClient.listCheckInSchedule.mockResolvedValue(
      schedulePage([scheduleEntry()], { total: 30 }),
    );
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");

    await user.click(screen.getByRole("button", { name: "Next page" }));
    await user.type(screen.getByRole("searchbox"), "ren");

    expect(apiClient.listCheckInSchedule).toHaveBeenCalledWith({
      search: "",
      page: 2,
    });
    expect(apiClient.listCheckInSchedule).toHaveBeenLastCalledWith({
      search: "ren",
      page: 1,
    });
  });

  it("pages through the Schedule", async () => {
    apiClient.listCheckInSchedule.mockResolvedValue(
      schedulePage([scheduleEntry()], { total: 30 }),
    );
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");

    expect(screen.getByText("Page 1 of 2")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Previous page" }),
    ).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Next page" }));

    expect(await screen.findByText("Page 2 of 2")).toBeVisible();
    expect(screen.getByRole("button", { name: "Next page" })).toBeDisabled();
  });

  it("says when nobody has opted in", async () => {
    apiClient.listCheckInSchedule.mockResolvedValue(schedulePage([]));
    renderWithQueries(<CheckInSchedule />);

    expect(
      await screen.findByText("No one has opted in to Check-ins yet"),
    ).toBeVisible();
  });

  it("opens a User's settings panel from their row", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");

    await user.click(
      within(rowFor("Ren Okafor")).getByRole("button", { name: "Edit" }),
    );

    expect(
      screen.getByRole("dialog", {
        name: "Check-in settings for Ren Okafor",
      }),
    ).toBeVisible();
  });

  it("offers a way to try again when it can't load", async () => {
    apiClient.listCheckInSchedule.mockRejectedValue(new Error("down"));
    renderWithQueries(<CheckInSchedule />);

    expect(
      await screen.findByText("Couldn’t load the Check-in Schedule"),
    ).toBeVisible();
  });

  it("asks for a Check in Now for the selected Users and shows each result", async () => {
    apiClient.checkInNow.mockResolvedValue([
      { user_id: "ren", result: "requested" },
      { user_id: "sam", result: "no_telegram_connection" },
    ]);
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");
    const checkInNow = screen.getByRole("button", { name: "Check in now" });
    expect(checkInNow).toBeDisabled();

    await user.click(
      screen.getByRole("checkbox", { name: "Select Ren Okafor" }),
    );
    await user.click(screen.getByRole("checkbox", { name: "Select Sam Lee" }));
    expect(screen.getByText(/2 selected/)).toBeVisible();
    await user.click(checkInNow);

    expect(apiClient.checkInNow).toHaveBeenCalledWith(["ren", "sam"]);
    const results = await screen.findByRole("status");
    expect(within(results).getByText(/1 of 2 requested/)).toBeVisible();
    expect(results).toHaveTextContent(
      "Ren Okafor: Requested — goes out on the next tick",
    );
    expect(results).toHaveTextContent(
      "Sam Lee: Refused — no Telegram Connection",
    );
    expect(
      screen.getByRole("checkbox", { name: "Select Ren Okafor" }),
    ).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Check in now" })).toBeDisabled();
  });

  it("selects everyone on the page at once, and clears them again", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");
    const wholePage = screen.getByRole("checkbox", {
      name: "Select everyone on this page",
    });

    await user.click(wholePage);
    expect(
      screen.getByRole("checkbox", { name: "Select Sam Lee" }),
    ).toBeChecked();
    expect(screen.getByText(/2 selected/)).toBeVisible();

    await user.click(wholePage);
    expect(
      screen.getByRole("checkbox", { name: "Select Ren Okafor" }),
    ).not.toBeChecked();
  });

  it("selecting a row doesn't open its settings panel", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");

    await user.click(
      screen.getByRole("checkbox", { name: "Select Ren Okafor" }),
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows when a Check in Now is already waiting for a User", async () => {
    apiClient.listCheckInSchedule.mockResolvedValue(
      schedulePage([scheduleEntry({ check_in_now_waiting: true })]),
    );
    renderWithQueries(<CheckInSchedule />);

    await screen.findByText("Ren Okafor");
    expect(
      within(rowFor("Ren Okafor")).getByText("Check in Now waiting"),
    ).toBeVisible();
  });

  it("says nothing was requested when the Check in Now fails", async () => {
    apiClient.checkInNow.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<CheckInSchedule />);
    await screen.findByText("Ren Okafor");

    await user.click(
      screen.getByRole("checkbox", { name: "Select Ren Okafor" }),
    );
    await user.click(screen.getByRole("button", { name: "Check in now" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nothing was requested",
    );
  });
});
