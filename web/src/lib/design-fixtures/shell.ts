import type { ApiClient, Me, PlatformContent } from "@/lib/api-client";

/** Alex, the User every User page in `design/reference/` is drawn for. */
export const alex: Me = {
  id: "design-alex",
  email: "alex@example.com",
  name: "Alex",
  onboarding_reasons: [],
  onboarding_note: null,
  country: "SG",
  time_zone: "Asia/Singapore",
  ai_notice_acknowledged_at: "2026-11-02T10:00:00+08:00",
  user_memory_enabled: true,
  user_memory_available: true,
  memory_note: "",
  photo_viewing_enabled: true,
  photo_viewing_available: true,
  personal_stickers_available: true,
  onboarding_completed_at: "2026-11-02T10:00:00+08:00",
  role: "user",
  changed_in_chat: {
    user_memory: "2026-11-12T21:00:00+08:00",
    quiet_hours: "2026-11-12T21:00:00+08:00",
  },
};

/** Zaf, the Admin every admin page in `design/reference/` is drawn for. */
export const zaf: Me = {
  ...alex,
  id: "design-zaf",
  email: "zaf@example.com",
  name: "Zaf",
  role: "admin",
  changed_in_chat: {},
};

/**
 * The Admin-worded content. The shell shows the short AI notice, as drawn in
 * the sidebar; the explanations and Delete my data text are as drawn in
 * `Account.html`.
 */
const platformContent: PlatformContent = {
  ai_notice: "",
  ai_notice_short: "Zeph is an AI, not a therapist or crisis service.",
  user_memory_explanation: [
    "So you don't have to repeat yourself, I can keep meaningful details: your goals, what helps you, the people you mention.",
    'You can see what I remember on your Dashboard and delete any of it, or tell me "forget that" in chat.',
    "I also keep a few private notes to follow up with you, like something to ask about later. You won't see these, and Delete My Data removes them along with everything else.",
  ].join("\n\n"),
  photo_viewing_explanation: [
    "When off, Zeph won't look at or remember your photos. Every photo is still checked for safety, so Zeph can share help if one looks worrying. Nothing from that check is kept.",
    "When on, Zeph looks at the photos you send and may keep the ones that matter to you, listed on your Memories page.",
  ].join("\n\n"),
  onboarding_reason_choices: [],
  message_retention_days: 30,
  delete_my_data_description:
    "Removes your messages, memories, the private notes Zeph keeps to follow up with you, Conversation Summaries, your stickers, Check-in history and Telegram Connection. Your account stays, so you can start fresh.",
};

/**
 * Builds the shell's fixtures: who is signed in, and the AI notice.
 *
 * @param signedIn - Alex, or Zaf when the browser asks to see the admin area.
 * @returns The fixture calls the shell needs.
 */
export function shellFixtures(signedIn: Me): Partial<ApiClient> {
  return {
    getMe: async () => signedIn,
    getPlatformContent: async () => platformContent,
  };
}
