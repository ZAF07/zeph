import type { ApiClient, PersonalSticker } from "@/lib/api-client";

/**
 * Alex's Personal Stickers, as drawn in `Account.html`. The reference draws
 * each as the dashed "Sticker" box, so none has an image or emoji.
 */
const personalStickers: PersonalSticker[] = [
  "Used when something goes well",
  "Used to say good night",
  "Used for a gentle nudge",
].map((note, index) => ({
  id: `design-sticker-${index + 1}`,
  emoji: null,
  note,
  has_image: false,
  kept_at: "2026-11-10T20:00:00+08:00",
}));

/**
 * Design fixtures for the Account reference pages. Values come only from
 * those reference files. Only the issue building this area fills it.
 */
export const accountFixtures: Partial<ApiClient> = {
  listPersonalStickers: async () => personalStickers,
};
