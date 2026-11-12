import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingGate } from "@/components/OnboardingGate";
import type { ApiClient, Me } from "@/lib/api-client";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
};
const router = { replace: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

function user(onboardingCompletedAt: string | null): Me {
  return {
    id: "user-1",
    email: "maya@example.com",
    name: null,
    onboarding_reasons: [],
    onboarding_note: null,
    country: null,
    time_zone: null,
    ai_notice_acknowledged_at: null,
    user_memory_enabled: true,
    onboarding_completed_at: onboardingCompletedAt,
    role: "user",
    changed_in_chat: {},
  };
}

describe("OnboardingGate", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("sends a User who has not finished onboarding to onboarding", async () => {
    apiClient.getMe.mockResolvedValue(user(null));

    render(<OnboardingGate>Connect Telegram page</OnboardingGate>);

    await vi.waitFor(() =>
      expect(router.replace).toHaveBeenCalledWith("/onboarding"),
    );
    expect(screen.queryByText("Connect Telegram page")).not.toBeInTheDocument();
  });

  it("shows the page to a User who has finished onboarding", async () => {
    apiClient.getMe.mockResolvedValue(user("2026-11-11T09:00:00Z"));

    render(<OnboardingGate>Connect Telegram page</OnboardingGate>);

    expect(
      await screen.findByText("Connect Telegram page"),
    ).toBeInTheDocument();
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("does not show the page when the check fails", async () => {
    apiClient.getMe.mockRejectedValue(new Error("down"));

    render(<OnboardingGate>Connect Telegram page</OnboardingGate>);

    expect(
      await screen.findByRole("button", { name: "Try again" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Connect Telegram page")).not.toBeInTheDocument();
  });
});
