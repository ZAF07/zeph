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

/** The signed-in User, with their profile and preferences. */
export type Me = {
  id: string;
  email: string | null;
  name: string | null;
  onboarding_reasons: string[];
  onboarding_note: string | null;
  country: string | null;
  time_zone: string | null;
  ai_notice_acknowledged_at: string | null;
  user_memory_enabled: boolean;
  onboarding_completed_at: string | null;
};

/** Everything a new User answers during onboarding. */
export type OnboardingAnswers = {
  name: string;
  ai_notice_acknowledged: boolean;
  onboarding_reasons: string[];
  onboarding_note: string | null;
  user_memory_enabled: boolean;
  country: string;
  time_zone: string;
};

/** Preferences to change; a field left out stays as it is. */
export type PreferenceChanges = {
  name?: string;
  user_memory_enabled?: boolean;
  country?: string;
  time_zone?: string;
};

/** Admin-managed wording the Dashboard shows to Users. */
export type PlatformContent = {
  ai_notice: string;
  ai_notice_short: string;
  user_memory_explanation: string;
  onboarding_reason_choices: string[];
};

/** Every call the Dashboard makes to the backend. */
export type ApiClient = {
  getMe: () => Promise<Me>;
  updatePreferences: (changes: PreferenceChanges) => Promise<Me>;
  completeOnboarding: (answers: OnboardingAnswers) => Promise<Me>;
  getPlatformContent: () => Promise<PlatformContent>;
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
  async function request<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const token = await getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    const response = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) {
      throw new ApiError(response.status, path);
    }
    return (await response.json()) as T;
  }

  return {
    getMe: () => request<Me>("/api/me"),
    updatePreferences: (changes) => request<Me>("/api/me", "PATCH", changes),
    completeOnboarding: (answers) =>
      request<Me>("/api/onboarding", "PUT", answers),
    getPlatformContent: () => request<PlatformContent>("/api/platform-content"),
    getTelegramConnection: () =>
      request<TelegramConnectionStatus>("/api/telegram-connection"),
    createConnectionToken: () =>
      request<ConnectionToken>("/api/telegram-connection/tokens", "POST"),
  };
}
