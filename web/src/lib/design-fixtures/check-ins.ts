import type { ApiClient, CheckIns } from "@/lib/api-client";

/** Alex's Check-ins, as drawn in `CheckIns.html` and `M-CheckIns.html`. */
const checkIns: CheckIns = {
  enabled: true,
  available: true,
  frequency: "few_times_a_week",
  quiet_hours_start: "23:00:00",
  quiet_hours_end: "07:00:00",
  paused: false,
  paused_until: null,
  recent: [
    {
      id: "design-check-in-1",
      outcome: "sent",
      kind: "A follow-up",
      decided_at: "2026-11-10T19:00:00+08:00",
      status: "replied",
      skipped_for_daily_limit: false,
    },
    {
      id: "design-check-in-2",
      outcome: "sent",
      kind: "A casual hello",
      decided_at: "2026-11-07T18:00:00+08:00",
      status: "no_reply",
      skipped_for_daily_limit: false,
    },
    {
      id: "design-check-in-3",
      outcome: "skipped",
      kind: null,
      decided_at: "2026-11-05T18:00:00+08:00",
      status: "skipped",
      skipped_for_daily_limit: false,
    },
    {
      id: "design-check-in-4",
      outcome: "sent",
      kind: "A thought to reflect on",
      decided_at: "2026-11-02T19:00:00+08:00",
      status: "replied",
      skipped_for_daily_limit: false,
    },
  ],
  kinds: [
    { name: "A casual hello", description: "Just checking how you are." },
    {
      name: "A follow-up",
      description: "On something you shared, like a decision or a hard day.",
    },
    {
      name: "A present-moment pause",
      description: "A brief invitation to notice where you are.",
    },
    {
      name: "A thought to reflect on",
      description: "An idea that might fit what is on your mind.",
    },
    {
      name: "A look back at a photo",
      description:
        "One of the photos you shared, sent back with a word about it.",
    },
    {
      name: "Something I've been wondering",
      description:
        "A question about something you mentioned, asked when the time is right.",
    },
  ],
  changed_by_admin: {},
};

/**
 * Design fixtures for the CheckIns reference pages. Values come only from
 * those reference files. Only the issue building this area fills it.
 */
export const checkInsFixtures: Partial<ApiClient> = {
  getCheckIns: async () => checkIns,
};
