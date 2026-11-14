import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SidebarAiNotice } from "@/components/SidebarAiNotice";
import type { ApiClient, PlatformContent } from "@/lib/api-client";
import { useSaveAdminSettings } from "@/lib/use-admin-settings";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function contentWithNotice(notice: string): PlatformContent {
  return {
    ai_notice: "",
    ai_notice_short: notice,
    onboarding_reason_choices: [],
    user_memory_explanation: "",
    photo_viewing_explanation: "",
    message_retention_days: 30,
    delete_my_data_description: "",
  };
}

function SaveNoticeButton() {
  const saveSettings = useSaveAdminSettings();
  return (
    <button
      type="button"
      onClick={() => saveSettings.mutate({ ai_notice_short: "New notice" })}
    >
      Save notice
    </button>
  );
}

describe("useSaveAdminSettings", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows saved wording in the User-facing parts of the page", async () => {
    apiClient.getPlatformContent
      .mockResolvedValueOnce(contentWithNotice("Old notice"))
      .mockResolvedValue(contentWithNotice("New notice"));
    apiClient.updateAdminSettings.mockResolvedValue({});
    const user = userEvent.setup();
    renderWithQueries(
      <>
        <SidebarAiNotice />
        <SaveNoticeButton />
      </>,
    );
    await screen.findByText("Old notice");

    await user.click(screen.getByRole("button", { name: "Save notice" }));

    expect(await screen.findByText("New notice")).toBeInTheDocument();
  });
});
