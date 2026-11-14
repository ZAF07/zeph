import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminGate } from "@/components/AdminGate";
import { OnboardingGate } from "@/components/OnboardingGate";
import { SidebarAdminBadge } from "@/components/SidebarAdminBadge";
import type { ApiClient, Me } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

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
    user_memory_available: true,
    memory_note: "",
    photo_viewing_enabled: true,
    photo_viewing_available: true,
    personal_stickers_available: false,
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

    renderWithQueries(<OnboardingGate>Connect Telegram page</OnboardingGate>);

    await vi.waitFor(() =>
      expect(router.replace).toHaveBeenCalledWith("/onboarding"),
    );
    expect(screen.queryByText("Connect Telegram page")).not.toBeInTheDocument();
  });

  it("shows the page to a User who has finished onboarding", async () => {
    apiClient.getMe.mockResolvedValue(user("2026-11-11T09:00:00Z"));

    renderWithQueries(<OnboardingGate>Connect Telegram page</OnboardingGate>);

    expect(
      await screen.findByText("Connect Telegram page"),
    ).toBeInTheDocument();
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("does not show the page when the check fails", async () => {
    apiClient.getMe.mockRejectedValue(new Error("down"));

    renderWithQueries(<OnboardingGate>Connect Telegram page</OnboardingGate>);

    expect(
      await screen.findByRole("button", { name: "Try again" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Connect Telegram page")).not.toBeInTheDocument();
  });

  it("loads the User once for the gates, the sidebar and the page", async () => {
    apiClient.getMe.mockResolvedValue({
      ...user("2026-11-11T09:00:00Z"),
      role: "admin",
    });

    renderWithQueries(
      <>
        <SidebarAdminBadge />
        <OnboardingGate>
          <AdminGate>Admin page</AdminGate>
        </OnboardingGate>
      </>,
    );

    expect(await screen.findByText("Admin page")).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
    expect(apiClient.getMe).toHaveBeenCalledTimes(1);
  });
});
