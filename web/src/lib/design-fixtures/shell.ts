import type { ApiClient, Me } from "@/lib/api-client";

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
  changed_in_chat: { user_memory: "2026-11-12T21:00:00+08:00" },
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
 * Builds the shell's fixtures: who is signed in.
 *
 * @param signedIn - Alex, or Zaf when the browser asks to see the admin area.
 * @returns The fixture calls the shell needs.
 */
export function shellFixtures(signedIn: Me): Partial<ApiClient> {
  return { getMe: async () => signedIn };
}
