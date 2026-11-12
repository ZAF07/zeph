import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountSettings } from "@/components/AccountSettings";
import {
  ApiError,
  type ApiClient,
  type Me,
  type PlatformContent,
} from "@/lib/api-client";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
  deleteMyData: vi.fn<ApiClient["deleteMyData"]>(),
  deleteAccount: vi.fn<ApiClient["deleteAccount"]>(),
};

const signOut = vi.fn<(redirectUrl: string) => Promise<void>>();

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

vi.mock("@/lib/auth/client", () => ({
  useSignOut: () => signOut,
}));

const content: PlatformContent = {
  ai_notice: "Seeded notice.",
  ai_notice_short: "Zeph is an AI.",
  user_memory_explanation: "Seeded memory explanation.",
  onboarding_reason_choices: [],
  message_retention_days: 14,
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
    apiClient.deleteMyData.mockResolvedValue(undefined);
    apiClient.deleteAccount.mockResolvedValue(undefined);
    signOut.mockResolvedValue(undefined);
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

  it("states the retention period from settings and that memories stay", async () => {
    render(<AccountSettings />);

    expect(
      await screen.findByText(
        "Messages are deleted automatically after 14 days. Summaries and memories stay until you delete them.",
      ),
    ).toBeInTheDocument();
  });

  it("deletes the User's data only after DELETE is typed", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);
    const yourData = within(
      await screen.findByRole("region", { name: "Your data" }),
    );

    await user.click(yourData.getByRole("button", { name: "Delete my data" }));
    const confirm = yourData.getByRole("button", { name: "Delete my data" });
    expect(confirm).toBeDisabled();
    await user.type(
      yourData.getByLabelText("Type DELETE to confirm"),
      "delete",
    );
    expect(confirm).toBeDisabled();
    await user.clear(yourData.getByLabelText("Type DELETE to confirm"));
    await user.type(
      yourData.getByLabelText("Type DELETE to confirm"),
      "DELETE",
    );
    await user.click(confirm);

    expect(apiClient.deleteMyData).toHaveBeenCalledTimes(1);
    expect(await yourData.findByRole("status")).toHaveTextContent(
      "Your data has been deleted.",
    );
    expect(apiClient.deleteAccount).not.toHaveBeenCalled();
  });

  it("cancelling Delete my data deletes nothing", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);
    const yourData = within(
      await screen.findByRole("region", { name: "Your data" }),
    );

    await user.click(yourData.getByRole("button", { name: "Delete my data" }));
    await user.click(yourData.getByRole("button", { name: "Cancel" }));

    expect(
      yourData.queryByLabelText("Type DELETE to confirm"),
    ).not.toBeInTheDocument();
    expect(apiClient.deleteMyData).not.toHaveBeenCalled();
  });

  it("tells the User when deleting their data fails", async () => {
    apiClient.deleteMyData.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<AccountSettings />);
    const yourData = within(
      await screen.findByRole("region", { name: "Your data" }),
    );

    await user.click(yourData.getByRole("button", { name: "Delete my data" }));
    await user.type(
      yourData.getByLabelText("Type DELETE to confirm"),
      "DELETE",
    );
    await user.click(yourData.getByRole("button", { name: "Delete my data" }));

    expect(await yourData.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete your data. Please try again.",
    );
  });

  it("deletes the account after DELETE is typed, then signs out", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);
    const deleteAccount = within(
      await screen.findByRole("region", { name: "Delete account" }),
    );

    await user.click(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    );
    const confirm = deleteAccount.getByRole("button", {
      name: "Permanently delete account",
    });
    expect(confirm).toBeDisabled();
    await user.type(
      deleteAccount.getByLabelText("Type DELETE to confirm"),
      "DELETE",
    );
    await user.click(confirm);

    expect(apiClient.deleteAccount).toHaveBeenCalledTimes(1);
    await vi.waitFor(() => expect(signOut).toHaveBeenCalledWith("/sign-in"));
    expect(apiClient.deleteMyData).not.toHaveBeenCalled();
  });

  it("keeps the account when the User chooses to", async () => {
    const user = userEvent.setup();
    render(<AccountSettings />);
    const deleteAccount = within(
      await screen.findByRole("region", { name: "Delete account" }),
    );

    await user.click(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    );
    await user.click(
      deleteAccount.getByRole("button", { name: "Keep my account" }),
    );

    expect(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    ).toBeInTheDocument();
    expect(apiClient.deleteAccount).not.toHaveBeenCalled();
  });

  it("shows why the last Admin can't delete their account, and stays signed in", async () => {
    apiClient.deleteAccount.mockRejectedValue(
      new ApiError(409, "/api/me", "You’re the only Admin."),
    );
    const user = userEvent.setup();
    render(<AccountSettings />);
    const deleteAccount = within(
      await screen.findByRole("region", { name: "Delete account" }),
    );

    await user.click(
      deleteAccount.getByRole("button", { name: "Delete my account" }),
    );
    await user.type(
      deleteAccount.getByLabelText("Type DELETE to confirm"),
      "DELETE",
    );
    await user.click(
      deleteAccount.getByRole("button", { name: "Permanently delete account" }),
    );

    expect(await deleteAccount.findByRole("alert")).toHaveTextContent(
      "You’re the only Admin.",
    );
    expect(signOut).not.toHaveBeenCalled();
  });
});
