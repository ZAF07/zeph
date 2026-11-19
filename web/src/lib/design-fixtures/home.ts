import type { ApiClient, Home } from "@/lib/api-client";
import { alex } from "@/lib/design-fixtures/shell";

/**
 * Alex's Dashboard home, as drawn in `Dashboard.html` and `M-Dashboard.html`.
 * The fixture clock stands at Tue 17 Nov 2026, 8:00 PM in Singapore, so the
 * last Conversation is "yesterday" and the last Check-in (Tue 10 Nov) is
 * "Tuesday".
 */
const home: Home = {
  name: alex.name,
  time_zone: alex.time_zone,
  telegram_connection: {
    telegram_username: "alex",
    connected_at: "2026-11-02T10:05:00+08:00",
  },
  telegram_chat_url: "#",
  last_conversation_at: "2026-11-16T21:30:00+08:00",
  check_ins: {
    enabled: true,
    available: true,
    frequency: "few_times_a_week",
    quiet_hours_start: "23:00:00",
    quiet_hours_end: "07:00:00",
    paused: false,
    paused_until: null,
    pause_changed_in_chat_at: null,
    last_sent: {
      id: "design-check-in-1",
      outcome: "sent",
      kind: "A follow-up",
      decided_at: "2026-11-10T19:00:00+08:00",
      status: "replied",
      skipped_for_daily_limit: false,
    },
  },
  user_memory_enabled: true,
  user_memory_available: true,
  goals: [
    {
      id: "design-goal-1",
      content: "Rest without feeling I am falling behind",
      source: "conversation",
      created_at: "2026-11-12T21:00:00+08:00",
      updated_at: "2026-11-12T21:00:00+08:00",
    },
    {
      id: "design-goal-2",
      content: "Decide about travelling in a van for a while",
      source: "conversation",
      created_at: "2026-11-09T20:00:00+08:00",
      updated_at: "2026-11-09T20:00:00+08:00",
    },
  ],
  recently_remembered: [
    {
      id: "design-memory-1",
      content: "Afraid that resting means losing ground",
      source: "conversation",
      created_at: "2026-11-16T21:30:00+08:00",
      updated_at: "2026-11-16T21:30:00+08:00",
      category: "Worries",
    },
    {
      id: "design-memory-2",
      content: "Has been pushing hard at work lately",
      source: "conversation",
      created_at: "2026-11-14T19:00:00+08:00",
      updated_at: "2026-11-14T19:00:00+08:00",
      category: "Work",
    },
    {
      id: "design-memory-3",
      content: "Wants more patience with his father",
      source: "conversation",
      created_at: "2026-11-12T21:00:00+08:00",
      updated_at: "2026-11-12T21:00:00+08:00",
      category: "Family",
    },
  ],
};

/**
 * Design fixtures for the Dashboard reference pages. Values come only from
 * those reference files. Only the issue building this area fills it.
 */
export const homeFixtures: Partial<ApiClient> = {
  getHome: async () => home,
};
