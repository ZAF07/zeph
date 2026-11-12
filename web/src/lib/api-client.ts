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

/** A setting a User can change by telling Zeph in chat. */
export type ChatSetting =
  | "check_in_pause"
  | "check_in_frequency"
  | "quiet_hours"
  | "user_memory"
  | "time_zone";

/**
 * The signed-in User, with their profile and preferences. `changed_in_chat`
 * says when each setting was last changed in chat; a setting changed on the
 * Dashboard since is left out.
 */
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
  changed_in_chat: Partial<Record<ChatSetting, string>>;
};

/** How often, at most, Zeph may send a Check-in. */
export type CheckInFrequency = "weekly" | "few_times_a_week" | "most_days";

/** How long to pause Check-ins for. */
export type PauseLength = "day" | "week" | "until_resumed";

/** What happened after a Check-in decision. */
export type CheckInStatus = "sent" | "replied" | "no_reply" | "skipped";

/** What Zeph decided for a Check-in: sent, skipped, or asked about fewer. */
export type CheckInOutcome = "sent" | "skipped" | "asked_about_fewer";

/** Everything a new User answers during onboarding. */
export type OnboardingAnswers = {
  name: string;
  ai_notice_acknowledged: boolean;
  onboarding_reasons: string[];
  onboarding_note: string | null;
  user_memory_enabled: boolean;
  country: string;
  time_zone: string;
  check_ins_enabled: boolean;
  check_in_frequency: CheckInFrequency;
  quiet_hours_start: string;
  quiet_hours_end: string;
};

/**
 * A Check-in Zeph sent or skipped, and whether the User replied. Never its
 * text or why it was skipped.
 */
export type RecentCheckIn = {
  id: string;
  outcome: CheckInOutcome;
  kind: string | null;
  decided_at: string;
  status: CheckInStatus;
};

/** A Check-in Kind as Users see it, read-only. */
export type CheckInKindSummary = {
  name: string;
  description: string;
};

/**
 * A User's Check-in settings and recent Check-ins. Quiet hours are local
 * times like "22:00:00"; `paused_until` is null while paused until resumed.
 * There is never a next Check-in time.
 */
export type CheckIns = {
  enabled: boolean;
  frequency: CheckInFrequency;
  quiet_hours_start: string;
  quiet_hours_end: string;
  paused: boolean;
  paused_until: string | null;
  recent: RecentCheckIn[];
  kinds: CheckInKindSummary[];
};

/** Check-in settings to change; a field left out stays as it is. */
export type CheckInChanges = {
  enabled?: boolean;
  frequency?: CheckInFrequency;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
};

/** Preferences to change; a field left out stays as it is. */
export type PreferenceChanges = {
  name?: string;
  user_memory_enabled?: boolean;
  country?: string;
  time_zone?: string;
};

/** Admin-managed wording and settings the Dashboard shows to Users. */
export type PlatformContent = {
  ai_notice: string;
  ai_notice_short: string;
  user_memory_explanation: string;
  onboarding_reason_choices: string[];
  message_retention_days: number;
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
export type SettingValue = string | number | boolean;

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

/** Where a Memory Item came from. */
export type MemorySource = "conversation" | "onboarding";

/** A single fact the Companion remembers about the User. */
export type MemoryItem = {
  id: string;
  content: string;
  source: MemorySource;
  created_at: string;
  updated_at: string;
};

/** The User's Memory Items in one Memory Category. */
export type MemoryGroup = {
  category: string;
  items: MemoryItem[];
};

/** A Memory Item with the name of its Memory Category. */
export type RememberedItem = MemoryItem & { category: string };

/**
 * A User's Check-in status for the Dashboard home, and the last Check-in
 * sent. `pause_changed_in_chat_at` says when the pause was last changed in
 * chat, if it was. There is never a next Check-in time.
 */
export type HomeCheckIns = {
  enabled: boolean;
  frequency: CheckInFrequency;
  quiet_hours_start: string;
  quiet_hours_end: string;
  paused: boolean;
  paused_until: string | null;
  pause_changed_in_chat_at: string | null;
  last_sent: RecentCheckIn | null;
};

/**
 * What the Dashboard home shows a User. `goals` and `recently_remembered`
 * are newest first, and empty while User Memory is off.
 */
export type Home = {
  name: string | null;
  time_zone: string | null;
  telegram_connection: TelegramConnection | null;
  telegram_chat_url: string;
  last_conversation_at: string | null;
  check_ins: HomeCheckIns;
  user_memory_enabled: boolean;
  goals: MemoryItem[];
  recently_remembered: RememberedItem[];
  ai_notice: string;
};

/** A short account of one Conversation and how the User seemed. */
export type ConversationSummary = {
  id: string;
  summary: string;
  mood: string;
  created_at: string;
};

/** A Check-in Kind's name, description and "allowed when memory is off". */
export type CheckInKindInput = {
  name: string;
  description: string;
  allowed_without_user_memory: boolean;
};

/** A Check-in Kind as Admins manage it. */
export type CheckInKind = CheckInKindInput & { id: string };

/** A Check-in Kind and how many Check-ins of it were sent in 30 days. */
export type CheckInKindOverview = CheckInKind & { sent_last_30_days: number };

/** One Check-in decision in the admin log. Never the message text. */
export type CheckInLogEntry = {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  decided_at: string;
  outcome: CheckInOutcome;
  kind: string | null;
  skip_reason: string | null;
  status: CheckInStatus;
};

/** What one User used on one of their days. Counts only, never content. */
export type DailyUsage = {
  day: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  message_count: number;
  tokens_in: number;
  tokens_out: number;
  web_search_count: number;
  message_limit_reached: boolean;
  web_search_limit_reached: boolean;
};

/** Usage per User per day, newest day first, with the limits in force now. */
export type UsageReport = {
  rows: DailyUsage[];
  daily_message_limit: number;
  web_search_daily_limit: number;
};

/** The kind of fact a Memory Item records, as Admins manage it. */
export type MemoryCategory = {
  id: string;
  name: string;
  description: string;
  always_include: boolean;
  archived: boolean;
};

/** A Memory Category and how many Memory Items, across all Users, it has. */
export type MemoryCategoryOverview = MemoryCategory & { item_count: number };

/** A Memory Category's name, description and "always include". */
export type MemoryCategoryInput = {
  name: string;
  description: string;
  always_include: boolean;
};

/** The kinds of file a Knowledge document can be. */
export type KnowledgeFileType = "text" | "markdown" | "pdf";

/** Where a Knowledge document is in being made ready for replies. */
export type KnowledgeStatus = "pending" | "ready" | "failed";

/** A document in the Knowledge library, without its file. */
export type KnowledgeDocument = {
  id: string;
  title: string;
  source: string;
  tradition: string;
  file_name: string;
  file_type: KnowledgeFileType;
  status: KnowledgeStatus;
  failure_reason: string | null;
  text_edited: boolean;
  created_at: string;
};

/** A Knowledge document with the text replies draw on; null until read. */
export type KnowledgeDocumentWithText = KnowledgeDocument & {
  text: string | null;
};

/** Details to change on a Knowledge document; a field left out is kept. */
export type KnowledgeDetailsChange = {
  title?: string;
  source?: string;
  tradition?: string;
};

/** A Knowledge document as an Admin uploads it. */
export type KnowledgeUpload = {
  file: File;
  title: string;
  source: string;
  tradition: string;
};

/** A sticker in the Sticker Library; Zeph only sends it once it has a note. */
export type Sticker = {
  id: string;
  emoji: string | null;
  set_name: string | null;
  note: string;
  has_image: boolean;
  added_at: string;
};

/** Every call the Dashboard makes to the backend. */
export type ApiClient = {
  getMe: () => Promise<Me>;
  updatePreferences: (changes: PreferenceChanges) => Promise<Me>;
  completeOnboarding: (answers: OnboardingAnswers) => Promise<Me>;
  deleteMyData: () => Promise<void>;
  deleteAccount: () => Promise<void>;
  getPlatformContent: () => Promise<PlatformContent>;
  getHome: () => Promise<Home>;
  getTelegramConnection: () => Promise<TelegramConnectionStatus>;
  createConnectionToken: () => Promise<ConnectionToken>;
  getCheckIns: () => Promise<CheckIns>;
  updateCheckIns: (changes: CheckInChanges) => Promise<CheckIns>;
  pauseCheckIns: (length: PauseLength) => Promise<CheckIns>;
  resumeCheckIns: () => Promise<CheckIns>;
  listMemoryGroups: () => Promise<MemoryGroup[]>;
  deleteMemoryItem: (id: string) => Promise<void>;
  deleteAllMemoryItems: () => Promise<void>;
  listConversationSummaries: () => Promise<ConversationSummary[]>;
  deleteConversationSummary: (id: string) => Promise<void>;
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
  listCheckInKinds: () => Promise<CheckInKindOverview[]>;
  addCheckInKind: (kind: CheckInKindInput) => Promise<CheckInKind>;
  updateCheckInKind: (
    id: string,
    kind: CheckInKindInput,
  ) => Promise<CheckInKind>;
  removeCheckInKind: (id: string) => Promise<void>;
  listCheckInLog: (days: number) => Promise<CheckInLogEntry[]>;
  getUsage: (days: number) => Promise<UsageReport>;
  listMemoryCategories: () => Promise<MemoryCategoryOverview[]>;
  addMemoryCategory: (category: MemoryCategoryInput) => Promise<MemoryCategory>;
  updateMemoryCategory: (
    id: string,
    category: MemoryCategoryInput,
  ) => Promise<MemoryCategory>;
  archiveMemoryCategory: (id: string) => Promise<MemoryCategory>;
  restoreMemoryCategory: (id: string) => Promise<MemoryCategory>;
  listKnowledgeDocuments: () => Promise<KnowledgeDocument[]>;
  getKnowledgeDocument: (id: string) => Promise<KnowledgeDocumentWithText>;
  updateKnowledgeDocumentDetails: (
    id: string,
    change: KnowledgeDetailsChange,
  ) => Promise<KnowledgeDocumentWithText>;
  saveKnowledgeDocumentText: (
    id: string,
    text: string,
  ) => Promise<KnowledgeDocumentWithText>;
  replaceKnowledgeDocumentFile: (
    id: string,
    file: File,
  ) => Promise<KnowledgeDocumentWithText>;
  uploadKnowledgeDocument: (
    upload: KnowledgeUpload,
  ) => Promise<KnowledgeDocument>;
  retryKnowledgeDocument: (id: string) => Promise<KnowledgeDocument>;
  deleteKnowledgeDocument: (id: string) => Promise<void>;
  listStickers: () => Promise<Sticker[]>;
  importStickerSet: (setName: string) => Promise<number>;
  saveStickerNote: (id: string, note: string) => Promise<Sticker>;
  removeSticker: (id: string) => Promise<void>;
  getStickerImage: (id: string) => Promise<Blob>;
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
  async function authHeaders(): Promise<Record<string, string>> {
    const token = await getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async function requestBlob(path: string): Promise<Blob> {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: await authHeaders(),
    });
    if (!response.ok) {
      throw new ApiError(response.status, path, await errorDetail(response));
    }
    return response.blob();
  }

  async function request<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const headers = await authHeaders();
    let requestBody: BodyInit | undefined;
    if (body instanceof FormData) {
      requestBody = body;
    } else if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      requestBody = JSON.stringify(body);
    }
    const response = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: requestBody,
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
    deleteMyData: () => request<void>("/api/me/data", "DELETE"),
    deleteAccount: () => request<void>("/api/me", "DELETE"),
    getPlatformContent: () => request<PlatformContent>("/api/platform-content"),
    getHome: () => request<Home>("/api/home"),
    getTelegramConnection: () =>
      request<TelegramConnectionStatus>("/api/telegram-connection"),
    createConnectionToken: () =>
      request<ConnectionToken>("/api/telegram-connection/tokens", "POST"),
    getCheckIns: () => request<CheckIns>("/api/check-ins"),
    updateCheckIns: (changes) =>
      request<CheckIns>("/api/check-ins", "PATCH", changes),
    pauseCheckIns: (length) =>
      request<CheckIns>("/api/check-ins/pause", "PUT", { length }),
    resumeCheckIns: () => request<CheckIns>("/api/check-ins/pause", "DELETE"),
    listMemoryGroups: async () =>
      (await request<{ groups: MemoryGroup[] }>("/api/memory-items")).groups,
    deleteMemoryItem: (id) =>
      request<void>(`/api/memory-items/${id}`, "DELETE"),
    deleteAllMemoryItems: () => request<void>("/api/memory-items", "DELETE"),
    listConversationSummaries: async () =>
      (
        await request<{ summaries: ConversationSummary[] }>(
          "/api/conversation-summaries",
        )
      ).summaries,
    deleteConversationSummary: (id) =>
      request<void>(`/api/conversation-summaries/${id}`, "DELETE"),
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
    listCheckInKinds: async () =>
      (
        await request<{ kinds: CheckInKindOverview[] }>(
          "/api/admin/check-in-kinds",
        )
      ).kinds,
    addCheckInKind: (kind) =>
      request<CheckInKind>("/api/admin/check-in-kinds", "POST", kind),
    updateCheckInKind: (id, kind) =>
      request<CheckInKind>(`/api/admin/check-in-kinds/${id}`, "PUT", kind),
    removeCheckInKind: (id) =>
      request<void>(`/api/admin/check-in-kinds/${id}`, "DELETE"),
    listCheckInLog: async (days) =>
      (
        await request<{ entries: CheckInLogEntry[] }>(
          `/api/admin/check-ins?days=${days}`,
        )
      ).entries,
    getUsage: (days) => request<UsageReport>(`/api/admin/usage?days=${days}`),
    listMemoryCategories: async () =>
      (
        await request<{ categories: MemoryCategoryOverview[] }>(
          "/api/admin/memory-categories",
        )
      ).categories,
    addMemoryCategory: (category) =>
      request<MemoryCategory>("/api/admin/memory-categories", "POST", category),
    updateMemoryCategory: (id, category) =>
      request<MemoryCategory>(
        `/api/admin/memory-categories/${id}`,
        "PUT",
        category,
      ),
    archiveMemoryCategory: (id) =>
      request<MemoryCategory>(
        `/api/admin/memory-categories/${id}/archive`,
        "POST",
      ),
    restoreMemoryCategory: (id) =>
      request<MemoryCategory>(
        `/api/admin/memory-categories/${id}/restore`,
        "POST",
      ),
    listKnowledgeDocuments: async () =>
      (
        await request<{ documents: KnowledgeDocument[] }>(
          "/api/admin/knowledge-documents",
        )
      ).documents,
    getKnowledgeDocument: (id) =>
      request<KnowledgeDocumentWithText>(
        `/api/admin/knowledge-documents/${id}`,
      ),
    updateKnowledgeDocumentDetails: (id, change) =>
      request<KnowledgeDocumentWithText>(
        `/api/admin/knowledge-documents/${id}`,
        "PATCH",
        change,
      ),
    saveKnowledgeDocumentText: (id, text) =>
      request<KnowledgeDocumentWithText>(
        `/api/admin/knowledge-documents/${id}/text`,
        "PUT",
        { text },
      ),
    replaceKnowledgeDocumentFile: (id, file) => {
      const form = new FormData();
      form.append("file", file);
      return request<KnowledgeDocumentWithText>(
        `/api/admin/knowledge-documents/${id}/file`,
        "PUT",
        form,
      );
    },
    uploadKnowledgeDocument: (upload) => {
      const form = new FormData();
      form.append("file", upload.file);
      form.append("title", upload.title);
      form.append("source", upload.source);
      form.append("tradition", upload.tradition);
      return request<KnowledgeDocument>(
        "/api/admin/knowledge-documents",
        "POST",
        form,
      );
    },
    retryKnowledgeDocument: (id) =>
      request<KnowledgeDocument>(
        `/api/admin/knowledge-documents/${id}/retry`,
        "POST",
      ),
    deleteKnowledgeDocument: (id) =>
      request<void>(`/api/admin/knowledge-documents/${id}`, "DELETE"),
    listStickers: async () =>
      (await request<{ stickers: Sticker[] }>("/api/admin/stickers")).stickers,
    importStickerSet: async (setName) =>
      (
        await request<{ added_count: number }>(
          "/api/admin/stickers/import",
          "POST",
          { set_name: setName },
        )
      ).added_count,
    saveStickerNote: (id, note) =>
      request<Sticker>(`/api/admin/stickers/${id}`, "PUT", { note }),
    removeSticker: (id) => request<void>(`/api/admin/stickers/${id}`, "DELETE"),
    getStickerImage: (id) => requestBlob(`/api/admin/stickers/${id}/image`),
  };
}
