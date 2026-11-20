import type {
  AdminUser,
  ApiClient,
  FeatureSwitch,
  UserFeatures,
} from "@/lib/api-client";

/** Builds a listed User; counts not drawn in `AdminUsers.html` are 0. */
function listedUser(
  user: Pick<
    AdminUser,
    | "id"
    | "name"
    | "email"
    | "signed_up_at"
    | "telegram_connected"
    | "conversation_count"
    | "messages_sent"
  > &
    Partial<AdminUser>,
): AdminUser {
  return {
    role: "user",
    life_thread_count: 0,
    move_outcome_count: 0,
    has_portrait: false,
    confirmed_pattern_count: 0,
    ...user,
  };
}

/** The Users drawn in `AdminUsers.html`, in order. */
const users: AdminUser[] = [
  listedUser({
    id: "design-alex-tan",
    name: "Alex Tan",
    email: "alex@example.com",
    signed_up_at: "2026-09-12T10:00:00+08:00",
    telegram_connected: true,
    conversation_count: 41,
    messages_sent: 612,
    life_thread_count: 6,
    move_outcome_count: 14,
    has_portrait: true,
    confirmed_pattern_count: 2,
  }),
  listedUser({
    id: "design-priya",
    name: "Priya Raman",
    email: "priya@example.com",
    signed_up_at: "2026-10-03T10:00:00+08:00",
    telegram_connected: true,
    conversation_count: 18,
    messages_sent: 240,
  }),
  listedUser({
    id: "design-marcus",
    name: "Marcus Lee",
    email: "marcus@example.com",
    signed_up_at: "2026-10-21T10:00:00+08:00",
    telegram_connected: true,
    conversation_count: 9,
    messages_sent: 131,
  }),
  listedUser({
    id: "design-jun",
    name: "Jun Wei",
    email: "jun@example.com",
    signed_up_at: "2026-11-02T10:00:00+08:00",
    telegram_connected: false,
    conversation_count: 0,
    messages_sent: 0,
  }),
  listedUser({
    id: "design-sara",
    name: "Sara Khan",
    email: "sara@example.com",
    role: "admin",
    signed_up_at: "2026-08-01T10:00:00+08:00",
    telegram_connected: true,
    conversation_count: 27,
    messages_sent: 388,
  }),
];

/** The Features drawn in Alex Tan's side panel. */
const userFeatures: UserFeatures = {
  features: [
    {
      feature: "web_search",
      name: "Web search",
      works: true,
      reason: "on_for_everyone",
      switch: "default",
      changed_by_email: null,
      changed_at: null,
    },
    {
      feature: "stickers",
      name: "Stickers",
      works: true,
      reason: "on_for_everyone",
      switch: "default",
      changed_by_email: null,
      changed_at: null,
    },
    {
      feature: "knowledge",
      name: "Knowledge",
      works: false,
      reason: "off_for_everyone",
      switch: "default",
      changed_by_email: null,
      changed_at: null,
    },
  ],
  personal_sticker_count: 4,
};

/** Everyone's switches, as Alex Tan's panel lines say. */
const everyoneFeatures: FeatureSwitch[] = userFeatures.features.map(
  (status) => ({
    feature: status.feature,
    name: status.name,
    description: "",
    on: status.works,
    changed_by_email: null,
    changed_at: null,
  }),
);

/**
 * Design fixtures for the AdminUsers reference pages. Values come only from
 * those reference files. Only the issue building this area fills it.
 */
export const adminUsersFixtures: Partial<ApiClient> = {
  listAdminUsers: async () => users,
  listUserFeatures: async () => userFeatures,
  listFeatures: async () => everyoneFeatures,
};
