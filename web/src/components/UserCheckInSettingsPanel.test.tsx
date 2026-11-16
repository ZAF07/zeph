import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserCheckInSettingsPanel } from "@/components/UserCheckInSettingsPanel";
import type { ApiClient } from "@/lib/api-client";
import { scheduleEntry } from "@/test/check-in-schedule";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  changeUserCheckIns: vi.fn<ApiClient["changeUserCheckIns"]>(),
  pauseUserCheckIns: vi.fn<ApiClient["pauseUserCheckIns"]>(),
  resumeUserCheckIns: vi.fn<ApiClient["resumeUserCheckIns"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

describe("UserCheckInSettingsPanel", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows the User's own frequency, Quiet Hours and pause", () => {
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={() => {}} />,
    );

    expect(screen.getByRole("button", { name: "Most days" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByLabelText("From")).toHaveValue("22:00");
    expect(screen.getByLabelText("Until")).toHaveValue("07:30");
    expect(screen.getByText("Not paused")).toBeVisible();
    expect(screen.getByText(/they’ll see “Changed by an Admin”/)).toBeVisible();
  });

  it("changes the User's frequency and shows the saved value", async () => {
    apiClient.changeUserCheckIns.mockResolvedValue(
      scheduleEntry({ frequency: "weekly" }),
    );
    const user = userEvent.setup();
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={() => {}} />,
    );

    await user.click(screen.getByRole("button", { name: "Once a week" }));

    expect(apiClient.changeUserCheckIns).toHaveBeenCalledWith("ren", {
      frequency: "weekly",
    });
    expect(
      await screen.findByRole("button", { name: "Once a week" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("changes the User's Quiet Hours", async () => {
    apiClient.changeUserCheckIns.mockResolvedValue(
      scheduleEntry({ quiet_hours_start: "21:00:00" }),
    );
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={() => {}} />,
    );
    fireEvent.change(screen.getByLabelText("From"), {
      target: { value: "21:00" },
    });

    await waitFor(() =>
      expect(apiClient.changeUserCheckIns).toHaveBeenCalledWith("ren", {
        quiet_hours_start: "21:00",
      }),
    );
    expect(await screen.findByLabelText("From")).toHaveValue("21:00");
  });

  it("pauses the User for a week and then resumes them", async () => {
    apiClient.pauseUserCheckIns.mockResolvedValue(
      scheduleEntry({ paused: true, paused_until: "2026-11-24T02:00:00Z" }),
    );
    apiClient.resumeUserCheckIns.mockResolvedValue(scheduleEntry());
    const user = userEvent.setup();
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={() => {}} />,
    );

    await user.click(screen.getByRole("button", { name: "For a week" }));
    expect(
      await screen.findByText("Paused until Tue 24 Nov 10:00"),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Resume" }));

    expect(apiClient.pauseUserCheckIns).toHaveBeenCalledWith("ren", "week");
    expect(apiClient.resumeUserCheckIns).toHaveBeenCalledWith("ren");
    expect(await screen.findByText("Not paused")).toBeVisible();
  });

  it("offers no way to turn the User's Check-ins on or off", () => {
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={() => {}} />,
    );

    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
    expect(
      screen.getByText(
        /To stop their Check-ins, turn the Check-ins Feature off/,
      ),
    ).toBeVisible();
  });

  it("says when a change couldn't be saved", async () => {
    apiClient.changeUserCheckIns.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={() => {}} />,
    );

    await user.click(screen.getByRole("button", { name: "Once a week" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t save that for Ren Okafor",
    );
  });

  it("closes with Escape", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithQueries(
      <UserCheckInSettingsPanel entry={scheduleEntry()} onClose={onClose} />,
    );

    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalled();
  });
});
