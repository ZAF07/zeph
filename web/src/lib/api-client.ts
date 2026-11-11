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

/** Whether a User is a plain User or an Admin. */
export type UserRole = "user" | "admin";

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
  role: UserRole;
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

/** A User as Admins see them: activity counts, never message text. */
export type AdminUser = {
  id: string;
  name: string | null;
  email: string | null;
  role: UserRole;
  signed_up_at: string;
  telegram_connected: boolean;
  conversation_count: number;
  messages_sent: number;
};

/** A User's role after a change. */
export type RoleChange = {
  id: string;
  role: UserRole;
};

/** The value of a platform setting Admins can edit. */
export type SettingValue = string | number;

/** A platform setting's value and when, and by whom, it was last saved. */
export type AdminSetting = {
  value: SettingValue;
  updated_at: string;
  updated_by: string | null;
};

/** Every platform setting Admins can edit, by key. */
export type AdminSettings = Record<string, AdminSetting>;

/** A core service whose prompt and model Admins can change. */
export type CoreService = {
  name: string;
  runs_when: string;
  description: string;
  prompt_key: string;
  model_key: string;
};

/** The core services and the models Admins can pick for them. */
export type CoreServices = {
  services: CoreService[];
  model_choices: string[];
};

/** A crisis support contact; the international fallback has no country. */
export type Helpline = {
  id: string;
  country: string | null;
  name: string;
  number: string;
  hours: string | null;
  sort_order: number;
};

/** A Helpline's name, number and hours, as an Admin enters them. */
export type HelplineDetails = {
  name: string;
  number: string;
  hours: string | null;
};

/** A country Helpline as an Admin enters it. */
export type HelplineInput = HelplineDetails & { country: string };

/** Every country's Helplines, by country and order, and the fallback. */
export type Helplines = {
  helplines: Helpline[];
  international_fallback: Helpline;
};

/** Which way to move a Helpline in its country's list. */
export type MoveDirection = "up" | "down";

/**
 * The kinds of crisis the Safeguard detects. "unclear" means the model twice
 * gave no answer, so it was treated as a crisis to be safe.
 */
export type RiskType =
  | "suicide_or_self_harm"
  | "danger_to_others"
  | "abuse"
  | "medical_emergency"
  | "unclear";

/** A Safeguard Event: who, when and what kind of risk. Never message text. */
export type SafeguardEvent = {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  risk_type: RiskType;
  created_at: string;
  helplines_country: string | null;
};

/** Which Safeguard Events to list; a field left out means no limit. */
export type SafeguardEventFilter = {
  riskType?: RiskType;
  days?: number;
};

/** Every call the Dashboard makes to the backend. */
export type ApiClient = {
  getMe: () => Promise<Me>;
  updatePreferences: (changes: PreferenceChanges) => Promise<Me>;
  completeOnboarding: (answers: OnboardingAnswers) => Promise<Me>;
  getPlatformContent: () => Promise<PlatformContent>;
  getTelegramConnection: () => Promise<TelegramConnectionStatus>;
  createConnectionToken: () => Promise<ConnectionToken>;
  listAdminUsers: () => Promise<AdminUser[]>;
  changeUserRole: (userId: string, role: UserRole) => Promise<RoleChange>;
  getAdminSettings: () => Promise<AdminSettings>;
  updateAdminSettings: (
    values: Record<string, SettingValue>,
  ) => Promise<AdminSettings>;
  getCoreServices: () => Promise<CoreServices>;
  listHelplines: () => Promise<Helplines>;
  addHelpline: (helpline: HelplineInput) => Promise<Helpline>;
  updateHelpline: (id: string, helpline: HelplineInput) => Promise<Helpline>;
  deleteHelpline: (id: string) => Promise<void>;
  moveHelpline: (id: string, direction: MoveDirection) => Promise<Helpline[]>;
  updateInternationalFallback: (details: HelplineDetails) => Promise<Helpline>;
  listSafeguardEvents: (
    filter: SafeguardEventFilter,
  ) => Promise<SafeguardEvent[]>;
};

/** Raised when the backend answers with an error status. */
export class ApiError extends Error {
  /**
   * @param status - The HTTP status code.
   * @param path - The API path that failed.
   * @param detail - The backend's explanation, when it gave one.
   */
  constructor(
    readonly status: number,
    path: string,
    readonly detail: string | null = null,
  ) {
    super(`API request to ${path} failed with status ${status}`);
  }
}

/**
 * Reads the backend's explanation from an error response, if it has one.
 *
 * @param response - The error response.
 * @returns The `detail` text, or null.
 */
async function errorDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof body.detail === "string"
    ) {
      return body.detail;
    }
  } catch {
    return null;
  }
  return null;
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
      throw new ApiError(response.status, path, await errorDetail(response));
    }
    if (response.status === 204) {
      return undefined as T;
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
    listAdminUsers: async () =>
      (await request<{ users: AdminUser[] }>("/api/admin/users")).users,
    changeUserRole: (userId, role) =>
      request<RoleChange>(`/api/admin/users/${userId}/role`, "PUT", { role }),
    getAdminSettings: async () =>
      (await request<{ settings: AdminSettings }>("/api/admin/settings"))
        .settings,
    updateAdminSettings: async (values) =>
      (
        await request<{ settings: AdminSettings }>(
          "/api/admin/settings",
          "PATCH",
          { values },
        )
      ).settings,
    getCoreServices: () => request<CoreServices>("/api/admin/core-services"),
    listHelplines: () => request<Helplines>("/api/admin/helplines"),
    addHelpline: (helpline) =>
      request<Helpline>("/api/admin/helplines", "POST", helpline),
    updateHelpline: (id, helpline) =>
      request<Helpline>(`/api/admin/helplines/${id}`, "PUT", helpline),
    deleteHelpline: (id) =>
      request<void>(`/api/admin/helplines/${id}`, "DELETE"),
    moveHelpline: async (id, direction) =>
      (
        await request<{ helplines: Helpline[] }>(
          `/api/admin/helplines/${id}/move`,
          "POST",
          { direction },
        )
      ).helplines,
    updateInternationalFallback: (details) =>
      request<Helpline>(
        "/api/admin/helplines/international-fallback",
        "PUT",
        details,
      ),
    listSafeguardEvents: async (filter) => {
      const query = new URLSearchParams();
      if (filter.riskType) {
        query.set("risk_type", filter.riskType);
      }
      if (filter.days) {
        query.set("days", String(filter.days));
      }
      const search = query.size > 0 ? `?${query.toString()}` : "";
      return (
        await request<{ events: SafeguardEvent[] }>(
          `/api/admin/safeguard-events${search}`,
        )
      ).events;
    },
  };
}
