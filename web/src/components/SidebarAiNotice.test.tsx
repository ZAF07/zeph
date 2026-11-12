import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SidebarAiNotice } from "@/components/SidebarAiNotice";
import type { ApiClient } from "@/lib/api-client";

const apiClient = {
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

describe("SidebarAiNotice", () => {
  it("shows the short AI notice from platform settings", async () => {
    apiClient.getPlatformContent.mockResolvedValue({
      ai_notice: "Long notice.",
      ai_notice_short: "Seeded: Zeph is an AI.",
      user_memory_explanation: "",
      onboarding_reason_choices: [],
      message_retention_days: 30,
    });

    render(<SidebarAiNotice />);

    expect(
      await screen.findByText("Seeded: Zeph is an AI."),
    ).toBeInTheDocument();
  });
});
