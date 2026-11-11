/** Where a connection token stands, as reported by the backend. */
export type ConnectionTokenStatus =
  "active" | "used" | "expired" | "connected_elsewhere";

/** A one-time code that connects Telegram, and how to use it. */
export type ConnectionToken = {
  token: string;
  deep_link_url: string;
  bot_username: string;
  expires_at: string;
  status: ConnectionTokenStatus;
};

/** A made Telegram Connection. */
export type TelegramConnection = {
  telegram_username: string | null;
  connected_at: string;
};

/** A User's Telegram Connection and their newest connection token. */
export type TelegramConnectionStatus = {
  connection: TelegramConnection | null;
  latest_token: ConnectionToken | null;
};

/** Every call the Dashboard makes to the backend. */
export type ApiClient = {
  getTelegramConnection: () => Promise<TelegramConnectionStatus>;
  createConnectionToken: () => Promise<ConnectionToken>;
};

/** Raised when the backend answers with an error status. */
export class ApiError extends Error {
  /**
   * @param status - The HTTP status code.
   * @param path - The API path that failed.
   */
  constructor(
    readonly status: number,
    path: string,
  ) {
    super(`API request to ${path} failed with status ${status}`);
  }
}

/**
 * Builds the one client every page uses to call the backend.
 *
 * @param baseUrl - The backend's public address.
 * @param getToken - Returns the signed-in User's session token.
 * @returns The API client.
 */
export function createApiClient(
  baseUrl: string,
  getToken: () => Promise<string | null>,
): ApiClient {
  async function request<T>(path: string, method = "GET"): Promise<T> {
    const token = await getToken();
    const response = await fetch(`${baseUrl}${path}`, {
      method,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new ApiError(response.status, path);
    }
    return (await response.json()) as T;
  }

  return {
    getTelegramConnection: () =>
      request<TelegramConnectionStatus>("/api/telegram-connection"),
    createConnectionToken: () =>
      request<ConnectionToken>("/api/telegram-connection/tokens", "POST"),
  };
}
