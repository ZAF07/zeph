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
  | "photo_viewing"
  | "time_zone";

/**
 * The signed-in User, with their profile and preferences. `changed_in_chat`
 * says when each setting was last changed in chat; a setting changed on the
 * Dashboard since is left out. `user_memory_available` and
 * `photo_viewing_available` are false when an Admin has that Feature off for
 * them, so they can't switch it. `memory_note` is the Admin-worded note
 * saying User Memory is off and why; "" while it works.
 * `personal_stickers_available` says whether
 * Personal Stickers works for them; they have no switch of their own.
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
  user_memory_available: boolean;
  memory_note: string;
  photo_viewing_enabled: boolean;
  photo_viewing_available: boolean;
  personal_stickers_available: boolean;
  onboarding_completed_at: string | null;
  role: UserRole;
  changed_in_chat: Partial<Record<ChatSetting, string>>;
};

/** How often, at most, Zeph may send a Check-in. */
export type CheckInFrequency =
  "weekly" | "few_times_a_week" | "most_days" | "a_few_times_a_day";

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
 * text or the Check-in model's reason for a skip; only whether it was skipped
 * because the User had reached the day's message limit.
 */
export type RecentCheckIn = {
  id: string;
  outcome: CheckInOutcome;
  kind: string | null;
  decided_at: string;
  status: CheckInStatus;
  skipped_for_daily_limit: boolean;
};

/** A Check-in Kind as Users see it, read-only. */
export type CheckInKindSummary = {
  name: string;
  description: string;
};

/**
 * A User's Check-in settings and recent Check-ins. Quiet hours are local
 * times like "22:00:00"; `paused_until` is null while paused until resumed.
 * `available` is false when an Admin has Check-ins off for them, so they
 * can't switch them. `changed_by_admin` says when an Admin last changed
 * each setting, until the User changes it. There is never a next Check-in
 * time.
 */
export type CheckIns = {
  enabled: boolean;
  available: boolean;
  frequency: CheckInFrequency;
  quiet_hours_start: string;
  quiet_hours_end: string;
  paused: boolean;
  paused_until: string | null;
  recent: RecentCheckIn[];
  kinds: CheckInKindSummary[];
  changed_by_admin: Partial<Record<ChatSetting, string>>;
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
  photo_viewing_enabled?: boolean;
  country?: string;
  time_zone?: string;
};

/** Admin-managed wording and settings the Dashboard shows to Users. */
export type PlatformContent = {
  ai_notice: string;
  ai_notice_short: string;
  user_memory_explanation: string;
  photo_viewing_explanation: string;
  onboarding_reason_choices: string[];
  message_retention_days: number;
  delete_my_data_description: string;
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
  life_thread_count: number;
  move_outcome_count: number;
  has_portrait: boolean;
};

/** A User's role after a change. */
export type RoleChange = {
  id: string;
  role: UserRole;
};

/** An extra the Companion offers that Admins can switch off. */
export type Feature =
  | "web_search"
  | "stickers"
  | "knowledge"
  | "check_ins"
  | "user_memory"
  | "settings_in_chat"
  | "photo_viewing"
  | "personal_stickers";

/** A Feature's switch for everyone and who last changed it, and when. */
export type FeatureSwitch = {
  feature: Feature;
  name: string;
  description: string;
  on: boolean;
  changed_by_email: string | null;
  changed_at: string | null;
};

/** An Admin's switch for one Feature for one User; "default" follows everyone's. */
export type UserFeatureSwitch = "default" | "on" | "off";

/** Why a Feature works, or doesn't, for a User right now. */
export type FeatureReason =
  | "on_for_everyone"
  | "on_for_user"
  | "off_for_everyone"
  | "off_for_user"
  | "turned_off_by_user"
  | "stickers_off";

/** Whether a Feature works for one User, why, and the Admin's switch for them. */
export type UserFeatureStatus = {
  feature: Feature;
  name: string;
  works: boolean;
  reason: FeatureReason;
  switch: UserFeatureSwitch;
  changed_by_email: string | null;
  changed_at: string | null;
};

/** Every Feature's status for one User, and how many Personal Stickers they have. */
export type UserFeatures = {
  features: UserFeatureStatus[];
  personal_sticker_count: number;
};

/** The value of a platform setting Admins can edit; the Check-in gaps are hours by frequency. */
export type SettingValue =
  string | number | boolean | Partial<Record<CheckInFrequency, number>>;

/** A platform setting's value and when, and by whom, it was last saved. */
export type AdminSetting = {
  value: SettingValue;
  updated_at: string;
  updated_by: string | null;
};

/** Every platform setting Admins can edit, by key. */
export type AdminSettings = Record<string, AdminSetting>;

/**
 * A text setting shown with a core service's prompt, e.g. a tool description.
 * `hint` says when it is used; null when it needs none.
 */
export type ExtraPrompt = {
  key: string;
  label: string;
  hint: string | null;
};

/** A named group of extra prompts on a core service's card. */
export type ExtraPromptGroup = {
  name: string;
  prompts: ExtraPrompt[];
};

/**
 * A core service whose prompt, model and thinking Admins can change.
 * `thinking_key` is the on/off setting for whether its model thinks first.
 */
export type CoreService = {
  name: string;
  runs_when: string;
  description: string;
  prompt_key: string;
  model_key: string;
  thinking_key: string;
  extra_prompts: ExtraPrompt[];
  extra_prompt_groups: ExtraPromptGroup[];
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
  available: boolean;
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
 * are newest first, shown whether or not User Memory is on. `memory_note`
 * is the Admin-worded note saying User Memory is off and why; "" while it
 * works.
 */
export type Home = {
  name: string | null;
  time_zone: string | null;
  telegram_connection: TelegramConnection | null;
  telegram_chat_url: string;
  last_conversation_at: string | null;
  check_ins: HomeCheckIns;
  memory_note: string;
  goals: MemoryItem[];
  recently_remembered: RememberedItem[];
  ai_notice: string;
};

/** A short account of one Conversation, how the User seemed and what Zeph offered. */
export type ConversationSummary = {
  id: string;
  summary: string;
  mood: string;
  offered: string;
  created_at: string;
};

/** Zeph's short picture of the User: who they are and what helps them. */
export type UserPortrait = {
  text: string;
  updated_at: string;
};

/** An ongoing story in the User's life that Zeph follows. */
export type LifeThread = {
  id: string;
  title: string;
  story: string;
  is_open: boolean;
  updated_at: string;
};

/** What Zeph learned about how one Move went: the moment, how and why. */
export type MoveOutcome = {
  id: string;
  move: string;
  role: "lead" | "support";
  situation: string;
  feeling: string;
  result: "helped" | "didnt_help" | "mixed";
  why: string;
  made_at: string;
};

/** A photo that matters to the User, kept in their User Memory. */
export type SharedPhoto = {
  id: string;
  description: string;
  note: string;
  caption: string;
  sent_at: string;
};

/** A sticker Zeph kept from the User, with when to use it. */
export type PersonalSticker = {
  id: string;
  emoji: string | null;
  note: string;
  has_image: boolean;
  kept_at: string;
};

/** A Check-in Kind's name and description. */
export type CheckInKindInput = {
  name: string;
  description: string;
};

/**
 * A Check-in Kind as Admins manage it. `sends_shared_photo` marks a Kind
 * that sends one of the User's Shared Photos and `raises_curiosity` one
 * that asks one of their Curiosities; Admins can't change either.
 */
export type CheckInKind = CheckInKindInput & {
  id: string;
  sends_shared_photo: boolean;
  raises_curiosity: boolean;
};

/** A Check-in Kind and how many Check-ins of it were sent in 30 days. */
export type CheckInKindOverview = CheckInKind & { sent_last_30_days: number };

/** A Need's name, when it fits and how to reply. */
export type NeedInput = {
  name: string;
  when_it_fits: string;
  how_to_reply: string;
};

/**
 * A Need as Admins manage it. `is_fallback` marks the one used when it
 * isn't clear what the User needs; it can be edited but not deleted.
 */
export type Need = NeedInput & {
  id: string;
  is_fallback: boolean;
};

/**
 * One Check-in decision in the admin log. Never the message text.
 * `requested_by` names the Admin who asked for it with Check in Now; null
 * for a scheduled one.
 */
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
  requested_by: string | null;
  woven_in: boolean;
};

/** Why a User's due Check-in is held back right now. */
export type HoldBackReason =
  | "check_ins_off"
  | "paused"
  | "quiet_hours"
  | "no_telegram_connection"
  | "waiting_to_be_woven_in"
  | "limit_skip_done_today"
  | "no_kind_to_send";

/** Why a due Check-in is held back, and until when; `until` is null when not known. */
export type HeldBack = {
  reason: HoldBackReason;
  until: string | null;
};

/**
 * One opted-in User on the Check-in Schedule. Never message content.
 * `next_due_at` is their Due Time; `held_back` is null unless the last tick
 * held a due Check-in back; `changed_by_admin` lists the settings an Admin
 * changed that the User hasn't changed since; `check_in_now_waiting` says an
 * Admin's Check in Now is waiting for the next tick.
 */
export type CheckInScheduleEntry = {
  user_id: string;
  name: string | null;
  email: string | null;
  time_zone: string | null;
  next_due_at: string | null;
  frequency: CheckInFrequency;
  quiet_hours_start: string;
  quiet_hours_end: string;
  paused: boolean;
  paused_until: string | null;
  check_ins_work: boolean;
  held_back: HeldBack | null;
  changed_by_admin: ChatSetting[];
  check_in_now_waiting: boolean;
};

/** What happened to a Check in Now asked for one User. */
export type CheckInNowResult =
  "requested" | "not_opted_in" | "no_telegram_connection";

/** One User's result from a Check in Now. */
export type CheckInNowResultForUser = {
  user_id: string;
  result: CheckInNowResult;
};

/** One page of the Check-in Schedule, and when the backend read it. */
export type CheckInSchedulePage = {
  entries: CheckInScheduleEntry[];
  total: number;
  page: number;
  page_size: number;
  now: string;
};

/** Which page of the Check-in Schedule to load. */
export type CheckInScheduleFilter = {
  search: string;
  page: number;
};

/** Check-in settings an Admin changes for a User; never the on/off switch. */
export type AdminCheckInChanges = {
  frequency?: CheckInFrequency;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
};

/** What a Model Call Log trace was for. */
export type TraceKind =
  "message" | "check_in" | "conversation_end" | "portrait_rewrite";

/** Which step of the Companion's work a model call was for. */
export type ModelStep =
  | "safeguard"
  | "understanding"
  | "reply"
  | "photo"
  | "check_in"
  | "conversation_end"
  | "life_threads"
  | "curiosities"
  | "move_outcomes"
  | "portrait"
  | "personal_stickers";

/** A Model Call Log trace in a list: who, when and totals. Never content. */
export type ModelCallTrace = {
  trace_id: string;
  kind: TraceKind;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  started_at: string;
  steps: ModelStep[];
  tokens_in: number;
  tokens_out: number;
  duration_ms: number;
  error_count: number;
  has_content: boolean;
};

/** What a model call was given and answered; kept only for Admins and Evals. */
export type ModelCallContent = {
  instructions: string;
  history: { role: string; text: string }[];
  tools_offered: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  }[];
  tool_calls: {
    name: string;
    arguments: Record<string, unknown>;
    result: string;
  }[];
  response: string;
  reasoning: string | null;
};

/** The shape of an Understanding: the Need, Move names and counts, never any words. */
export type UnderstandingShape = {
  need: string;
  lead_move: string | null;
  support_move: string | null;
  intensity: "low" | "medium" | "high";
  cause_known: boolean;
  threads_reminded: number;
  threads_led_with: number;
  threads_woven_in: number;
  threads_left_alone: number;
  threads_held_back: number;
  past_look_ups: number;
};

/** The shape of a woven-in Check-in decision: counts and the Kind, never any words. */
export type CheckInShape = {
  kinds_offered: number;
  woven_in: boolean;
  kind: string | null;
};

/** One model call in a trace; `content` is null unless it was kept. */
export type ModelCall = {
  id: string;
  step: ModelStep;
  model: string;
  thinking: boolean;
  started_at: string;
  duration_ms: number;
  tokens_in: number;
  tokens_out: number;
  error: string | null;
  tools_called: string[];
  content: ModelCallContent | null;
  understanding_shape: UnderstandingShape | null;
  check_in_shape: CheckInShape | null;
};

/** One Model Call Log trace with every call in it, in order. */
export type ModelCallTraceDetails = ModelCallTrace & { calls: ModelCall[] };

/** Which traces to list; a field left out means no limit. */
export type ModelCallTraceFilter = {
  userId?: string;
  days?: number;
  step?: ModelStep;
  errorsOnly?: boolean;
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
  /** When it fits what a User needs, as the Understanding reads it; "" until drafted. */
  when_it_helps: string;
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
  when_it_helps?: string;
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

/** One of the six Evals. */
export type EvalName =
  | "safeguard"
  | "persona"
  | "knowledge"
  | "settings"
  | "photo_descriptions"
  | "understanding";

/** An Eval and the cases a new run of it would run. */
export type EvalSummary = { eval: EvalName; case_keys: string[] };

/** Where an Eval Run stands. */
export type EvalRunState =
  | "queued"
  | "running"
  | "finished"
  | "cancelled"
  | "stopped_over_limit"
  | "interrupted";

/** How one Eval Case went; an Error couldn't be checked and isn't a Fail. */
export type CaseOutcome = "pass" | "fail" | "error";

/**
 * An Eval Run with its totals so far. `started_by_name` is null for a run
 * started from the terminal. `cost_sgd` leaves out the tokens of
 * `unpriced_models`, which have no Model Price. `token_limit` is null until
 * the runner takes the run.
 */
export type EvalRun = {
  id: string;
  state: EvalRunState;
  started_from: "dashboard" | "terminal";
  started_by_name: string | null;
  evals: EvalName[];
  repeats: number;
  variants: EvalVariant[];
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  case_count: number;
  case_keys: string[];
  cancel_requested: boolean;
  token_limit: number | null;
  rerun_of: string | null;
  passed: number;
  failed: number;
  errored: number;
  tokens_in: number;
  tokens_out: number;
  cost_sgd: number;
  unpriced_models: string[];
};

/** The whole Evals and single cases a run runs. */
export type EvalRunPick = { evals: EvalName[]; case_keys: string[] };

/**
 * A Variant's Setting Overrides, by setting key, or `need:<id>` for a Need
 * (its name, when it fits and how to reply).
 */
export type SettingOverrides = Record<string, unknown>;

/**
 * Who made a Variant live, when, and which overrides were applied or left
 * out. `by_name` is null if the Admin has since gone.
 */
export type MadeLive = {
  by_name: string | null;
  at: string;
  applied_keys: string[];
  left_out_keys: string[];
};

/** One set of settings a run runs its cases with; null `made_live` if never. */
export type EvalVariant = {
  letter: string;
  setting_overrides: SettingOverrides;
  made_live: MadeLive | null;
};

/**
 * A new run: its cases, each Variant's Setting Overrides (lettered A, B, C;
 * an empty one runs the live settings) and how many times each case runs.
 */
export type EvalRunRequest = EvalRunPick & {
  variants: SettingOverrides[];
  repeats: number;
};

/** What kind of value a Platform Setting holds. */
export type SettingKind = "text" | "whole_number" | "model" | "on_off";

/** A Platform Setting a Variant can override, with its rule and live value. */
export type OverridableSetting = {
  key: string;
  label: string;
  kind: SettingKind;
  minimum: number;
  maximum: number;
  max_length: number;
  hint: string | null;
  value: unknown;
};

/** A Need as an override's value. */
export type NeedOverride = {
  name: string;
  when_it_fits: string;
  how_to_reply: string;
};

/** A Need a Variant can override, keyed `need:<id>`, with its live details. */
export type OverridableNeed = {
  key: string;
  name: string;
  value: NeedOverride;
};

/** What a Variant can override, and the models a model setting can pick. */
export type OverrideChoices = {
  settings: OverridableSetting[];
  needs: OverridableNeed[];
  models: string[];
};

/**
 * An overridden setting whose live value changed since the run started;
 * `now` is null for a Need deleted since.
 */
export type LiveChange = {
  key: string;
  then: unknown;
  now: unknown;
  override: unknown;
};

/**
 * What a run would use, before it starts; only an estimate. `cost_sgd`
 * leaves out the tokens of `unpriced_models`. `rough_case_count` cases have
 * never run, so use a rough figure for their Eval.
 */
export type EvalRunEstimate = {
  case_count: number;
  rough_case_count: number;
  tokens_in: number;
  tokens_out: number;
  models: { model: string; tokens_in: number; tokens_out: number }[];
  cost_sgd: number;
  unpriced_models: string[];
  variants: {
    letter: string;
    tokens_in: number;
    tokens_out: number;
    cost_sgd: number;
    unpriced_models: string[];
  }[];
};

/**
 * One thing checked in a case, such as a Judge rule and its reason. `group`
 * names the Message it checks in an Understanding case; "" otherwise.
 */
export type CaseCheck = {
  name: string;
  passed: boolean;
  detail: string;
  group: string;
};

/** One case's result in an Eval Run. */
export type CaseResult = {
  id: string;
  variant: string;
  try_number: number;
  case_key: string;
  eval: EvalName;
  outcome: CaseOutcome;
  checks: CaseCheck[];
  notes: string[];
  error: string;
  tokens_in: number;
  tokens_out: number;
  duration_ms: number;
  finished_at: string;
};

/** How one Variant's finished cases went, added up. */
export type VariantTotals = {
  letter: string;
  passed: number;
  failed: number;
  errored: number;
  tokens_in: number;
  tokens_out: number;
  duration_ms: number;
  cost_sgd: number;
  unpriced_models: string[];
};

/**
 * An Eval Run with its Case Results so far, in the order they finished, and
 * each Variant's totals.
 */
export type EvalRunDetails = EvalRun & {
  results: CaseResult[];
  variant_totals: VariantTotals[];
};

/** What kind of value a field of a case or Judge form holds. */
export type FieldKind =
  | "text"
  | "long_text"
  | "whole_number"
  | "on_off"
  | "choice"
  | "date_time"
  | "image"
  | "text_list"
  | "group"
  | "group_list";

/** One value a choice field can hold. */
export type ChoiceOption = { value: string | boolean; label: string };

/**
 * One field of a form, as the backend describes it: what it holds, what it
 * means and, for a group or list of groups, its own fields.
 */
export type ShapeField = {
  name: string;
  label: string;
  description: string;
  kind: FieldKind;
  required: boolean;
  options: ChoiceOption[];
  fields: ShapeField[];
  unique_by: string;
  item_label: string;
  minimum: number | null;
  default: unknown;
};

/** A part of a form, such as the made-up User Memory. */
export type ShapeSection = {
  title: string;
  description: string;
  fields: ShapeField[];
};

/** The fields a case, or the Judge's settings, is made of, in sections. */
export type FormShape = { sections: ShapeSection[] };

/** A form's values, by field name. */
export type FormValues = Record<string, unknown>;

/** An Eval Case as Admins see it. */
export type EvalCase = {
  key: string;
  eval: EvalName;
  content: FormValues;
  archived: boolean;
  edited: boolean;
  updated_at: string;
  updated_by_name: string | null;
};

/** The Judge's settings and the form that edits them. */
export type JudgeSettings = { shape: FormShape; values: FormValues };
/** A Case Result with its full trace: every model call its case made. */
export type CaseResultTrace = {
  run_id: string;
  result: CaseResult;
  calls: ModelCall[];
};

/** An Eval Case, as it is or as it was when a run started. */
export type EvalCaseContent = {
  key: string;
  eval: EvalName;
  content: Record<string, unknown>;
  archived: boolean;
};

/**
 * What a run used; every field is null while it is Queued. `needs` are the
 * live Needs, keyed as their overrides would be.
 */
export type EvalRunSnapshot = {
  settings: Record<string, unknown> | null;
  judge: Record<string, unknown> | null;
  cases: EvalCaseContent[] | null;
  needs: OverridableNeed[] | null;
};

/**
 * A case's result in one run. `case_changed` and `changed_settings` say what
 * was different from the older result after it in the list; Judge settings
 * show as `judge.<name>`.
 */
export type CaseHistoryEntry = {
  run_id: string;
  run_queued_at: string;
  result_id: string;
  variant: string;
  try_number: number;
  outcome: CaseOutcome;
  case_changed: boolean;
  changed_settings: string[];
};

/** A case and its results in recent runs, newest first. */
export type CaseHistory = {
  case: EvalCaseContent;
  entries: CaseHistoryEntry[];
};

/** One model's price in SGD per 1M tokens; null for no price set. */
export type ModelPrice = {
  model: string;
  sgd_in: number | null;
  sgd_out: number | null;
};

/** The Model Prices and the Eval run token limit. */
export type EvalCosts = { prices: ModelPrice[]; token_limit: number };

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
  listLifeThreads: () => Promise<LifeThread[]>;
  deleteLifeThread: (id: string) => Promise<void>;
  listMoveOutcomes: () => Promise<MoveOutcome[]>;
  deleteMoveOutcome: (id: string) => Promise<void>;
  getUserPortrait: () => Promise<UserPortrait | null>;
  deleteUserPortrait: () => Promise<void>;
  listSharedPhotos: () => Promise<SharedPhoto[]>;
  getSharedPhotoImage: (id: string) => Promise<Blob>;
  deleteSharedPhoto: (id: string) => Promise<void>;
  listPersonalStickers: () => Promise<PersonalSticker[]>;
  getPersonalStickerImage: (id: string) => Promise<Blob>;
  deletePersonalSticker: (id: string) => Promise<void>;
  listAdminUsers: () => Promise<AdminUser[]>;
  changeUserRole: (userId: string, role: UserRole) => Promise<RoleChange>;
  listFeatures: () => Promise<FeatureSwitch[]>;
  setFeatureForEveryone: (
    feature: Feature,
    on: boolean,
  ) => Promise<FeatureSwitch>;
  listUserFeatures: (userId: string) => Promise<UserFeatures>;
  setFeatureForUser: (
    userId: string,
    feature: Feature,
    featureSwitch: UserFeatureSwitch,
  ) => Promise<UserFeatureStatus>;
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
  listNeeds: () => Promise<Need[]>;
  addNeed: (need: NeedInput) => Promise<Need>;
  updateNeed: (id: string, need: NeedInput) => Promise<Need>;
  deleteNeed: (id: string) => Promise<void>;
  moveNeed: (id: string, direction: MoveDirection) => Promise<Need[]>;
  listCheckInLog: (days: number) => Promise<CheckInLogEntry[]>;
  listCheckInSchedule: (
    filter: CheckInScheduleFilter,
  ) => Promise<CheckInSchedulePage>;
  changeUserCheckIns: (
    userId: string,
    changes: AdminCheckInChanges,
  ) => Promise<CheckInScheduleEntry>;
  pauseUserCheckIns: (
    userId: string,
    length: PauseLength,
  ) => Promise<CheckInScheduleEntry>;
  resumeUserCheckIns: (userId: string) => Promise<CheckInScheduleEntry>;
  checkInNow: (userIds: string[]) => Promise<CheckInNowResultForUser[]>;
  listModelCallTraces: (
    filter: ModelCallTraceFilter,
  ) => Promise<ModelCallTrace[]>;
  getModelCallTrace: (traceId: string) => Promise<ModelCallTraceDetails>;
  listEvals: () => Promise<EvalSummary[]>;
  listEvalRuns: (includeTerminal: boolean) => Promise<EvalRun[]>;
  startEvalRun: (request: EvalRunRequest) => Promise<EvalRun>;
  estimateEvalRun: (request: EvalRunRequest) => Promise<EvalRunEstimate>;
  listSettingOverrideChoices: () => Promise<OverrideChoices>;
  listLiveChanges: (runId: string, letter: string) => Promise<LiveChange[]>;
  makeVariantLive: (
    runId: string,
    letter: string,
    confirmedKeys: string[],
  ) => Promise<EvalVariant>;
  getEvalRun: (runId: string) => Promise<EvalRunDetails>;
  listEvalCaseShapes: () => Promise<Record<EvalName, FormShape>>;
  listEvalCases: (evalName: EvalName) => Promise<EvalCase[]>;
  getEvalCase: (key: string) => Promise<EvalCase>;
  addEvalCase: (
    key: string,
    evalName: EvalName,
    content: FormValues,
  ) => Promise<EvalCase>;
  editEvalCase: (key: string, content: FormValues) => Promise<EvalCase>;
  duplicateEvalCase: (key: string, newKey: string) => Promise<EvalCase>;
  archiveEvalCase: (key: string) => Promise<EvalCase>;
  uploadEvalImage: (file: File) => Promise<{ name: string }>;
  getEvalImage: (name: string) => Promise<Blob>;
  getJudgeSettings: () => Promise<JudgeSettings>;
  saveJudgeSettings: (values: FormValues) => Promise<JudgeSettings>;
  cancelEvalRun: (runId: string) => Promise<EvalRun>;
  rerunFailedCases: (runId: string) => Promise<EvalRun>;
  deleteEvalRun: (runId: string) => Promise<void>;
  getEvalRunSnapshot: (runId: string) => Promise<EvalRunSnapshot>;
  getCaseResultTrace: (
    runId: string,
    resultId: string,
  ) => Promise<CaseResultTrace>;
  getCaseHistory: (caseKey: string) => Promise<CaseHistory>;
  getEvalCosts: () => Promise<EvalCosts>;
  saveEvalCosts: (costs: EvalCosts) => Promise<EvalCosts>;
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
   * @param fields - What is wrong per form field, by the field's path
   *   (e.g. `messages.0.text`), when a form save was refused.
   */
  constructor(
    readonly status: number,
    path: string,
    readonly detail: string | null = null,
    readonly fields: Record<string, string> = {},
  ) {
    super(`API request to ${path} failed with status ${status}`);
  }
}

/**
 * Reads the per-field messages from a refused form save's body.
 *
 * @param body - The parsed error body.
 * @returns Each field's message by its path; empty when there are none.
 */
function fieldErrors(body: object): Record<string, string> {
  if (!("fields" in body) || typeof body.fields !== "object" || !body.fields) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(body.fields).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
}

/**
 * Turns an error response into an `ApiError` with the backend's
 * explanation and per-field messages, if it gave them.
 *
 * @param response - The error response.
 * @param path - The API path that failed.
 * @returns The error.
 */
async function toApiError(response: Response, path: string): Promise<ApiError> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null) {
      const detail =
        "detail" in body && typeof body.detail === "string"
          ? body.detail
          : null;
      return new ApiError(response.status, path, detail, fieldErrors(body));
    }
  } catch {
    return new ApiError(response.status, path);
  }
  return new ApiError(response.status, path);
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
      throw await toApiError(response, path);
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
      throw await toApiError(response, path);
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
    listLifeThreads: async () =>
      (await request<{ threads: LifeThread[] }>("/api/life-threads")).threads,
    deleteLifeThread: (id) =>
      request<void>(`/api/life-threads/${id}`, "DELETE"),
    listMoveOutcomes: async () =>
      (await request<{ move_outcomes: MoveOutcome[] }>("/api/move-outcomes"))
        .move_outcomes,
    deleteMoveOutcome: (id) =>
      request<void>(`/api/move-outcomes/${id}`, "DELETE"),
    getUserPortrait: async () =>
      (await request<{ portrait: UserPortrait | null }>("/api/user-portrait"))
        .portrait,
    deleteUserPortrait: () => request<void>("/api/user-portrait", "DELETE"),
    listSharedPhotos: async () =>
      (await request<{ photos: SharedPhoto[] }>("/api/shared-photos")).photos,
    getSharedPhotoImage: (id) => requestBlob(`/api/shared-photos/${id}/image`),
    deleteSharedPhoto: (id) =>
      request<void>(`/api/shared-photos/${id}`, "DELETE"),
    listPersonalStickers: async () =>
      (await request<{ stickers: PersonalSticker[] }>("/api/personal-stickers"))
        .stickers,
    getPersonalStickerImage: (id) =>
      requestBlob(`/api/personal-stickers/${id}/image`),
    deletePersonalSticker: (id) =>
      request<void>(`/api/personal-stickers/${id}`, "DELETE"),
    listAdminUsers: async () =>
      (await request<{ users: AdminUser[] }>("/api/admin/users")).users,
    changeUserRole: (userId, role) =>
      request<RoleChange>(`/api/admin/users/${userId}/role`, "PUT", { role }),
    listFeatures: async () =>
      (await request<{ features: FeatureSwitch[] }>("/api/admin/features"))
        .features,
    setFeatureForEveryone: (feature, on) =>
      request<FeatureSwitch>(`/api/admin/features/${feature}`, "PUT", { on }),
    listUserFeatures: (userId) =>
      request<UserFeatures>(`/api/admin/users/${userId}/features`),
    setFeatureForUser: (userId, feature, featureSwitch) =>
      request<UserFeatureStatus>(
        `/api/admin/users/${userId}/features/${feature}`,
        "PUT",
        { switch: featureSwitch },
      ),
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
    listNeeds: async () =>
      (await request<{ needs: Need[] }>("/api/admin/needs")).needs,
    addNeed: (need) => request<Need>("/api/admin/needs", "POST", need),
    updateNeed: (id, need) =>
      request<Need>(`/api/admin/needs/${id}`, "PUT", need),
    deleteNeed: (id) => request<void>(`/api/admin/needs/${id}`, "DELETE"),
    moveNeed: async (id, direction) =>
      (
        await request<{ needs: Need[] }>(
          `/api/admin/needs/${id}/move`,
          "POST",
          { direction },
        )
      ).needs,
    listCheckInLog: async (days) =>
      (
        await request<{ entries: CheckInLogEntry[] }>(
          `/api/admin/check-ins?days=${days}`,
        )
      ).entries,
    listCheckInSchedule: (filter) => {
      const query = new URLSearchParams({
        search: filter.search,
        page: String(filter.page),
      });
      return request<CheckInSchedulePage>(
        `/api/admin/check-in-schedule?${query.toString()}`,
      );
    },
    changeUserCheckIns: (userId, changes) =>
      request<CheckInScheduleEntry>(
        `/api/admin/check-in-schedule/${userId}`,
        "PATCH",
        changes,
      ),
    pauseUserCheckIns: (userId, length) =>
      request<CheckInScheduleEntry>(
        `/api/admin/check-in-schedule/${userId}/pause`,
        "PUT",
        { length },
      ),
    resumeUserCheckIns: (userId) =>
      request<CheckInScheduleEntry>(
        `/api/admin/check-in-schedule/${userId}/pause`,
        "DELETE",
      ),
    checkInNow: async (userIds) =>
      (
        await request<{ results: CheckInNowResultForUser[] }>(
          "/api/admin/check-in-schedule/check-in-now",
          "POST",
          { user_ids: userIds },
        )
      ).results,
    listModelCallTraces: async (filter) => {
      const query = new URLSearchParams();
      if (filter.userId) {
        query.set("user_id", filter.userId);
      }
      if (filter.days) {
        query.set("days", String(filter.days));
      }
      if (filter.step) {
        query.set("step", filter.step);
      }
      if (filter.errorsOnly) {
        query.set("errors_only", "true");
      }
      const search = query.size > 0 ? `?${query.toString()}` : "";
      return (
        await request<{ traces: ModelCallTrace[] }>(
          `/api/admin/model-calls${search}`,
        )
      ).traces;
    },
    getModelCallTrace: (traceId) =>
      request<ModelCallTraceDetails>(`/api/admin/model-calls/${traceId}`),
    listEvals: async () =>
      (await request<{ evals: EvalSummary[] }>("/api/admin/evals")).evals,
    listEvalRuns: async (includeTerminal) =>
      (
        await request<{ runs: EvalRun[] }>(
          `/api/admin/eval-runs?include_terminal=${includeTerminal}`,
        )
      ).runs,
    startEvalRun: (runRequest) =>
      request<EvalRun>("/api/admin/eval-runs", "POST", runRequest),
    estimateEvalRun: (runRequest) =>
      request<EvalRunEstimate>(
        "/api/admin/eval-runs/estimate",
        "POST",
        runRequest,
      ),
    listSettingOverrideChoices: () =>
      request<OverrideChoices>("/api/admin/setting-override-choices"),
    listLiveChanges: async (runId, letter) =>
      (
        await request<{ changes: LiveChange[] }>(
          `/api/admin/eval-runs/${runId}/variants/${letter}/live-changes`,
        )
      ).changes,
    makeVariantLive: (runId, letter, confirmedKeys) =>
      request<EvalVariant>(
        `/api/admin/eval-runs/${runId}/variants/${letter}/make-live`,
        "POST",
        { confirmed_keys: confirmedKeys },
      ),
    getEvalRun: (runId) =>
      request<EvalRunDetails>(`/api/admin/eval-runs/${runId}`),
    listEvalCaseShapes: async () =>
      (
        await request<{ shapes: Record<EvalName, FormShape> }>(
          "/api/admin/eval-case-shapes",
        )
      ).shapes,
    listEvalCases: async (evalName) =>
      (
        await request<{ cases: EvalCase[] }>(
          `/api/admin/eval-cases?eval=${evalName}`,
        )
      ).cases,
    getEvalCase: (key) =>
      request<EvalCase>(`/api/admin/eval-cases/${encodeURIComponent(key)}`),
    addEvalCase: (key, evalName, content) =>
      request<EvalCase>("/api/admin/eval-cases", "POST", {
        key,
        eval: evalName,
        content,
      }),
    editEvalCase: (key, content) =>
      request<EvalCase>(
        `/api/admin/eval-cases/${encodeURIComponent(key)}`,
        "PUT",
        { content },
      ),
    duplicateEvalCase: (key, newKey) =>
      request<EvalCase>(
        `/api/admin/eval-cases/${encodeURIComponent(key)}/duplicate`,
        "POST",
        { key: newKey },
      ),
    archiveEvalCase: (key) =>
      request<EvalCase>(
        `/api/admin/eval-cases/${encodeURIComponent(key)}/archive`,
        "POST",
      ),
    uploadEvalImage: (file) => {
      const form = new FormData();
      form.append("file", file);
      return request<{ name: string }>("/api/admin/eval-images", "POST", form);
    },
    getEvalImage: (name) =>
      requestBlob(`/api/admin/eval-images/${encodeURIComponent(name)}`),
    getJudgeSettings: () => request<JudgeSettings>("/api/admin/eval-judge"),
    saveJudgeSettings: (values) =>
      request<JudgeSettings>("/api/admin/eval-judge", "PUT", { values }),
    cancelEvalRun: (runId) =>
      request<EvalRun>(`/api/admin/eval-runs/${runId}/cancel`, "POST"),
    rerunFailedCases: (runId) =>
      request<EvalRun>(`/api/admin/eval-runs/${runId}/rerun-failed`, "POST"),
    deleteEvalRun: (runId) =>
      request<void>(`/api/admin/eval-runs/${runId}`, "DELETE"),
    getEvalRunSnapshot: (runId) =>
      request<EvalRunSnapshot>(`/api/admin/eval-runs/${runId}/snapshot`),
    getCaseResultTrace: (runId, resultId) =>
      request<CaseResultTrace>(
        `/api/admin/eval-runs/${runId}/results/${resultId}`,
      ),
    getCaseHistory: (caseKey) =>
      request<CaseHistory>(
        `/api/admin/eval-cases/${encodeURIComponent(caseKey)}/history`,
      ),
    getEvalCosts: () => request<EvalCosts>("/api/admin/eval-costs"),
    saveEvalCosts: (costs) =>
      request<EvalCosts>("/api/admin/eval-costs", "PUT", costs),
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
