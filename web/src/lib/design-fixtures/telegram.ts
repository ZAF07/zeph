import type { ApiClient, ConnectionToken } from "@/lib/api-client";

/** How long the drawn Telegram link has left. */
const LINK_MINUTES_LEFT = 14;

/**
 * Builds the link drawn on the ConnectTelegram reference pages, so it always
 * has the drawn minutes left.
 *
 * @returns The active link.
 */
function drawnLink(): ConnectionToken {
  return {
    token: "7QK2-M9PX",
    deep_link_url: "https://t.me/zeph_bot?start=7QK2-M9PX",
    bot_username: "zeph_bot",
    expires_at: new Date(Date.now() + LINK_MINUTES_LEFT * 60000).toISOString(),
    status: "active",
  };
}

/**
 * Design fixtures for the ConnectTelegram reference pages. Values come only from
 * those reference files. Only the issue building this area fills it.
 */
export const telegramFixtures: Partial<ApiClient> = {
  getTelegramConnection: async () => ({
    connection: null,
    latest_token: drawnLink(),
  }),
  createConnectionToken: async () => drawnLink(),
};
