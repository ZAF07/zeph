import type {
  ApiClient,
  CheckIns,
  Me,
  PlatformContent,
} from "@/lib/api-client";
import { alex } from "@/lib/design-fixtures/shell";
import { hasDesignFlag } from "@/lib/design-flags";

/** Alex before onboarding, with the answers drawn on each step. */
const newAlex: Me = {
  ...alex,
  name: null,
  onboarding_reasons: [
    "Making sense of a decision",
    "Living more deliberately",
  ],
  ai_notice_acknowledged_at: null,
  onboarding_completed_at: null,
  changed_in_chat: {},
};

/** The Check-ins step: on, a few times a week, quiet 11 PM to 7 AM. */
const checkIns: CheckIns = {
  enabled: true,
  available: true,
  frequency: "few_times_a_week",
  quiet_hours_start: "23:00:00",
  quiet_hours_end: "07:00:00",
  paused: false,
  paused_until: null,
  recent: [],
  kinds: [],
  changed_by_admin: {},
};

/** The Admin-worded text the steps show. The AI notice is a placeholder. */
const platformContent: PlatformContent = {
  ai_notice: "[AI NOTICE, WORDED BY ADMINS IN PLATFORM SETTINGS]",
  ai_notice_short: "Zeph is an AI, not a therapist or crisis service.",
  user_memory_explanation: [
    "So you don't have to repeat yourself, I can keep meaningful details: your goals, what helps you, the people you mention.",
    'You can see what I remember on your Dashboard and delete any of it, or tell me "forget that" in chat.',
    "I also keep a few private notes to follow up with you, like something to ask about later. You won't see these, and Delete My Data removes them along with everything else.",
  ].join("\n\n"),
  photo_viewing_explanation: "",
  onboarding_reason_choices: [
    "Being more present",
    "Making sense of a decision",
    "Understanding myself",
    "Calmer under pressure",
    "Relationships",
    "Finding direction and values",
    "Exploring philosophy",
    "Living more deliberately",
  ],
  message_retention_days: 30,
  delete_my_data_description: "",
};

/** How long the drawn Telegram link has left. */
const LINK_MINUTES_LEFT = 14;

/**
 * Design fixtures for the Onboarding reference pages. Values come only from
 * those reference files. They apply only on the `?design=all-steps` address,
 * so every other page keeps the shell's Alex, who has finished onboarding.
 *
 * @param address - The page's query string, like "?design=all-steps".
 * @returns The fixture calls, or none away from the all-steps address.
 */
export function onboardingFixtures(address: string): Partial<ApiClient> {
  if (!hasDesignFlag(new URLSearchParams(address), "all-steps", true)) {
    return {};
  }
  return {
    getMe: async () => newAlex,
    getCheckIns: async () => checkIns,
    getPlatformContent: async () => platformContent,
    getTelegramConnection: async () => ({
      connection: null,
      latest_token: {
        token: "7QK2-M9PX",
        deep_link_url: "https://t.me/zeph_bot?start=7QK2-M9PX",
        bot_username: "zeph_bot",
        expires_at: new Date(
          Date.now() + LINK_MINUTES_LEFT * 60000,
        ).toISOString(),
        status: "active",
      },
    }),
  };
}
