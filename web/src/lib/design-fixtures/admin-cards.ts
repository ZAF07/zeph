import type { ApiClient, CheckInKindOverview } from "@/lib/api-client";

/** The six Check-in Kinds drawn in AdminCheckInKinds, in order. */
const checkInKinds: CheckInKindOverview[] = [
  {
    id: "kind-casual-hello",
    name: "A casual hello",
    description:
      "Just checking how you are. Light, no agenda, easy to ignore without guilt.",
    sends_shared_photo: false,
    raises_curiosity: false,
    shares_pattern: false,
    sent_last_30_days: 58,
  },
  {
    id: "kind-follow-up",
    name: "A follow-up",
    description:
      "On something the user shared, like a decision or a hard day. Only when there is something specific to return to.",
    sends_shared_photo: false,
    raises_curiosity: false,
    shares_pattern: false,
    sent_last_30_days: 41,
  },
  {
    id: "kind-present-moment",
    name: "A present-moment pause",
    description: "A brief invitation to notice where you are right now.",
    sends_shared_photo: false,
    raises_curiosity: false,
    shares_pattern: false,
    sent_last_30_days: 22,
  },
  {
    id: "kind-thought",
    name: "A thought to reflect on",
    description: "An idea that might fit what is on the user’s mind.",
    sends_shared_photo: false,
    raises_curiosity: false,
    shares_pattern: false,
    sent_last_30_days: 37,
  },
  {
    id: "kind-photo",
    name: "A look back at a photo",
    description:
      "One of the photos the user shared, sent back with a word about it.",
    sends_shared_photo: true,
    raises_curiosity: false,
    shares_pattern: false,
    sent_last_30_days: 9,
  },
  {
    id: "kind-wondering",
    name: "Something I've been wondering",
    description:
      "A question about something the user mentioned, asked when the time is right.",
    sends_shared_photo: false,
    raises_curiosity: true,
    shares_pattern: false,
    sent_last_30_days: 14,
  },
];

/**
 * Design fixtures for the AdminCheckInKinds (the card-list template) reference
 * pages. Values come only from those reference files. Only the issue
 * building this area fills it.
 */
export const adminCardsFixtures: Partial<ApiClient> = {
  listCheckInKinds: () => Promise.resolve(checkInKinds),
};
