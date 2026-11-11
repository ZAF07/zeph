import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CrisisReplyEditor } from "@/components/CrisisReplyEditor";
import { ApiError, type AdminSettings, type ApiClient } from "@/lib/api-client";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const settings: AdminSettings = {
  crisis_reply: {
    value: "I’m an AI. Please reach out:\n{helplines}",
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  },
};

describe("CrisisReplyEditor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getAdminSettings.mockResolvedValue(settings);
    apiClient.updateAdminSettings.mockImplementation(async (values) => ({
      crisis_reply: {
        value: String(values.crisis_reply),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
    }));
  });

  it("shows the saved Crisis Reply wording", async () => {
    render(<CrisisReplyEditor />);

    expect(await screen.findByLabelText("Crisis Reply wording")).toHaveValue(
      "I’m an AI. Please reach out:\n{helplines}",
    );
    expect(screen.getByText("Using the starting values")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Save Crisis Reply" }),
    ).toBeDisabled();
  });

  it("saves new wording", async () => {
    const user = userEvent.setup();
    render(<CrisisReplyEditor />);
    const wording = await screen.findByLabelText("Crisis Reply wording");

    await user.type(wording, " I’m still here.");
    await user.click(screen.getByRole("button", { name: "Save Crisis Reply" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      crisis_reply: "I’m an AI. Please reach out:\n{helplines} I’m still here.",
    });
    expect(await screen.findByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(screen.getByText("Saved")).toBeVisible();
  });

  it("shows why the backend refused the wording", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/settings",
        "The Crisis Reply must include {helplines}, where the Helplines go.",
      ),
    );
    const user = userEvent.setup();
    render(<CrisisReplyEditor />);
    const wording = await screen.findByLabelText("Crisis Reply wording");

    await user.clear(wording);
    await user.type(wording, "Please get help.");
    await user.click(screen.getByRole("button", { name: "Save Crisis Reply" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The Crisis Reply must include {helplines}, where the Helplines go.",
    );
  });

  it("won't save blank wording", async () => {
    const user = userEvent.setup();
    render(<CrisisReplyEditor />);

    await user.clear(await screen.findByLabelText("Crisis Reply wording"));

    expect(
      screen.getByRole("button", { name: "Save Crisis Reply" }),
    ).toBeDisabled();
  });

  it("offers Try again when the wording cannot be loaded", async () => {
    apiClient.getAdminSettings
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(settings);
    const user = userEvent.setup();
    render(<CrisisReplyEditor />);

    expect(
      await screen.findByText("Couldn’t load the Crisis Reply"),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(
      await screen.findByLabelText("Crisis Reply wording"),
    ).toBeInTheDocument();
  });
});
