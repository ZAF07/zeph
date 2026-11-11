import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountSettings } from "@/components/AccountSettings";
import type { ApiClient, Me, PlatformContent } from "@/lib/api-client";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const content: PlatformContent = {
  ai_notice: "Seeded notice.",
  ai_notice_short: "Zeph is an AI.",
  user_memory_explanation: "Seeded memory explanation.",
  onboarding_reason_choices: [],
};

const onboardedUser: Me = {
  id: "user-1",
  email: "maya@example.com",
  name: "Maya",
  onboarding_reasons: ["Relationships"],
  onboarding_note: null,
  country: "SG",
  time_zone: "Asia/Singapore",
  ai_notice_acknowledged_at: "2026-11-11T09:00:00Z",
  user_memory_enabled: true,
  onboarding_completed_at: "2026-11-11T09:00:00Z",
  role: "user",
};

describe("AccountSettings", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getMe.mockResolvedValue(onboardedUser);
    apiClient.getPlatformContent.mockResolvedValue(content);
    apiClient.updatePreferences.mockImplementation(async (changes) => ({
      ...onboardedUser,
      ...changes,
    }));
  });

  it("shows the saved profile", async () => {
    render(<AccountSettings />);

    expect(await screen.findByLabelText("What Zeph calls you")).toHaveValue(
      "Maya",
    );
    expect(screen.getByText("maya@example.com")).toBeInTheDocument();
    expect(screen.getByLabelText("Country")).toHaveValue("SG");
    expect(screen.getByLabelText("Time zone")).toHaveValue("Asia/Singapore");
  });

  it("saves a changed name, country and time zone", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);
    const nameField = await screen.findByLabelText("What Zeph calls you");

    await user.clear(nameField);
    await user.type(nameField, "May");
    await user.selectOptions(screen.getByLabelText("Country"), ["GB"]);
    await user.selectOptions(screen.getByLabelText("Time zone"), [
      "Europe/London",
    ]);
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      name: "May",
      country: "GB",
      time_zone: "Europe/London",
    });
  });

  it("does not save an empty name", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);

    await user.clear(await screen.findByLabelText("What Zeph calls you"));

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("tells the User when saving the profile fails", async () => {
    apiClient.updatePreferences.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<AccountSettings />);

    await user.click(
      await screen.findByRole("button", { name: "Save changes" }),
    );

    expect(
      await screen.findByText("We couldn’t save that. Please try again."),
    ).toBeInTheDocument();
  });

  it("turns User Memory off straight away, with the seeded explanation", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);
    const memorySwitch = await screen.findByRole("switch", {
      name: "Remember meaningful details",
    });

    expect(screen.getByText("Seeded memory explanation.")).toBeInTheDocument();
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");

    await user.click(memorySwitch);

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      user_memory_enabled: false,
    });
    await vi.waitFor(() =>
      expect(memorySwitch).toHaveAttribute("aria-checked", "false"),
    );
  });

  it("offers Try again when the account cannot be loaded", async () => {
    apiClient.getMe.mockRejectedValueOnce(new Error("down"));
    const user = userEvent.setup();
    render(<AccountSettings />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByLabelText("What Zeph calls you"),
    ).toBeInTheDocument();
  });
});
