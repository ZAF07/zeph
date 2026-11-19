import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ApiClient, PlatformContent } from "@/lib/api-client";
import { usePlatformContent } from "@/lib/queries";
import { useSaveAdminSettings } from "@/lib/use-admin-settings";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function contentWithRetention(days: number): PlatformContent {
  return { onboarding_reason_choices: [], message_retention_days: days };
}

function RetentionDays() {
  const days = usePlatformContent().data?.message_retention_days;
  return days === undefined ? null : <p>{`Kept ${days} days`}</p>;
}

function SaveRetentionButton() {
  const saveSettings = useSaveAdminSettings();
  return (
    <button
      type="button"
      onClick={() => saveSettings.mutate({ message_retention_days: 14 })}
    >
      Save retention
    </button>
  );
}

describe("useSaveAdminSettings", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows saved settings in the User-facing parts of the page", async () => {
    apiClient.getPlatformContent
      .mockResolvedValueOnce(contentWithRetention(30))
      .mockResolvedValue(contentWithRetention(14));
    apiClient.updateAdminSettings.mockResolvedValue({});
    const user = userEvent.setup();
    renderWithQueries(
      <>
        <RetentionDays />
        <SaveRetentionButton />
      </>,
    );
    await screen.findByText("Kept 30 days");

    await user.click(screen.getByRole("button", { name: "Save retention" }));

    expect(await screen.findByText("Kept 14 days")).toBeInTheDocument();
  });
});
