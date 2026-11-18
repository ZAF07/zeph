import { describe, expect, it } from "vitest";

import { onboardingFixtures } from "@/lib/design-fixtures/onboarding";

describe("onboardingFixtures", () => {
  it("gives nothing outside the all-steps address", () => {
    expect(onboardingFixtures("")).toEqual({});
    expect(onboardingFixtures("?design=menu-open")).toEqual({});
  });

  it("gives a new User with the answers drawn on the all-steps sheet", async () => {
    const fixtures = onboardingFixtures("?design=all-steps");

    expect(await fixtures.getMe?.()).toMatchObject({
      name: null,
      ai_notice_acknowledged_at: null,
      onboarding_completed_at: null,
      onboarding_reasons: [
        "Making sense of a decision",
        "Living more deliberately",
      ],
      country: "SG",
      time_zone: "Asia/Singapore",
      user_memory_enabled: true,
    });
    expect(await fixtures.getCheckIns?.()).toMatchObject({
      enabled: true,
      frequency: "few_times_a_week",
      quiet_hours_start: "23:00:00",
      quiet_hours_end: "07:00:00",
    });
  });

  it("gives a Telegram link that expires in 14 minutes", async () => {
    const fixtures = onboardingFixtures("?design=all-steps");

    const status = await fixtures.getTelegramConnection?.();
    const expiresAt = new Date(status?.latest_token?.expires_at ?? 0);
    const minutesLeft = (expiresAt.getTime() - Date.now()) / 60000;

    expect(status?.connection).toBeNull();
    expect(status?.latest_token?.status).toBe("active");
    expect(Math.ceil(minutesLeft)).toBe(14);
  });
});
