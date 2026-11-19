import type {
  ApiClient,
  CheckInLogEntry,
  CheckInScheduleEntry,
  DailyUsage,
  EvalCase,
  EvalRun,
  ModelCallTrace,
  SafeguardEvent,
} from "@/lib/api-client";

/** Builds a log entry; fields not drawn in `AdminCheckInLog.html` are empty. */
function logEntry(
  entry: Pick<
    CheckInLogEntry,
    "id" | "user_name" | "decided_at" | "outcome" | "status"
  > &
    Partial<CheckInLogEntry>,
): CheckInLogEntry {
  return {
    user_id: `user-${entry.id}`,
    user_email: null,
    kind: null,
    skip_reason: null,
    requested_by: null,
    woven_in: false,
    ...entry,
  };
}

/** The Check-in log rows drawn in `AdminCheckInLog.html`, newest first. */
const checkInLog: CheckInLogEntry[] = [
  logEntry({
    id: "log-1",
    user_name: "Alex Tan",
    decided_at: "2026-11-17T18:42:00+08:00",
    outcome: "sent",
    kind: "A follow-up",
    status: "replied",
  }),
  logEntry({
    id: "log-2",
    user_name: "Priya Raman",
    decided_at: "2026-11-17T14:10:00+08:00",
    outcome: "skipped",
    skip_reason: "Inside quiet hours",
    status: "skipped",
  }),
  logEntry({
    id: "log-3",
    user_name: "Marcus Lee",
    decided_at: "2026-11-17T09:05:00+08:00",
    outcome: "sent",
    kind: "A casual hello",
    woven_in: true,
    status: "sent",
  }),
  logEntry({
    id: "log-4",
    user_name: "Sara Khan",
    decided_at: "2026-11-16T20:30:00+08:00",
    outcome: "sent",
    kind: "A thought to reflect on",
    requested_by: "Zaf",
    status: "no_reply",
  }),
  logEntry({
    id: "log-5",
    user_name: "Alex Tan",
    decided_at: "2026-11-16T13:15:00+08:00",
    outcome: "skipped",
    skip_reason: "Talked with Zeph recently",
    status: "skipped",
  }),
  logEntry({
    id: "log-6",
    user_name: "Marcus Lee",
    decided_at: "2026-11-15T19:48:00+08:00",
    outcome: "asked_about_fewer",
    status: "skipped",
  }),
];

/**
 * Safeguard Events for the page built from the table template. It has no
 * reference of its own, so the people are the ones the template draws.
 */
const safeguardEvents: SafeguardEvent[] = [
  {
    id: "event-1",
    user_id: "user-priya",
    user_name: "Priya Raman",
    user_email: null,
    risk_type: "suicide_or_self_harm",
    created_at: "2026-11-17T22:14:00+08:00",
    helplines_country: "SG",
  },
  {
    id: "event-2",
    user_id: "user-marcus",
    user_name: "Marcus Lee",
    user_email: null,
    risk_type: "abuse",
    created_at: "2026-11-12T08:40:00+08:00",
    helplines_country: null,
  },
];

/** Builds a Check-in Schedule row; fields not shown are plain defaults. */
function scheduleEntry(
  entry: Pick<CheckInScheduleEntry, "user_id" | "name" | "email"> &
    Partial<CheckInScheduleEntry>,
): CheckInScheduleEntry {
  return {
    time_zone: "Asia/Singapore",
    next_due_at: "2026-11-18T13:00:00+08:00",
    frequency: "most_days",
    quiet_hours_start: "22:00:00",
    quiet_hours_end: "07:30:00",
    paused: false,
    paused_until: null,
    check_ins_work: true,
    held_back: null,
    changed_by_admin: [],
    check_in_now_waiting: false,
    ...entry,
  };
}

/** The Check-in Schedule, soonest Due Time first. */
const checkInSchedule: CheckInScheduleEntry[] = [
  scheduleEntry({
    user_id: "user-alex",
    name: "Alex Tan",
    email: "alex@example.com",
    check_in_now_waiting: true,
  }),
  scheduleEntry({
    user_id: "user-sara",
    name: "Sara Khan",
    email: "sara@example.com",
    next_due_at: "2026-11-19T09:00:00+08:00",
    frequency: "few_times_a_week",
    held_back: { reason: "quiet_hours", until: "2026-11-19T07:30:00+08:00" },
  }),
  scheduleEntry({
    user_id: "user-marcus",
    name: "Marcus Lee",
    email: "marcus@example.com",
    next_due_at: null,
    frequency: "weekly",
    paused: true,
    paused_until: null,
    check_ins_work: false,
  }),
];

/** Builds a usage row; fields not shown are zero. */
function usageRow(
  row: Pick<DailyUsage, "user_id" | "user_name"> & Partial<DailyUsage>,
): DailyUsage {
  return {
    day: "2026-11-18",
    user_email: null,
    message_count: 0,
    tokens_in: 0,
    tokens_out: 0,
    web_search_count: 0,
    message_limit_reached: false,
    web_search_limit_reached: false,
    ...row,
  };
}

/** Today's usage, one row per User. */
const usageRows: DailyUsage[] = [
  usageRow({
    user_id: "user-alex",
    user_name: "Alex Tan",
    message_count: 24,
    tokens_in: 31240,
    tokens_out: 3880,
    web_search_count: 1,
  }),
  usageRow({
    user_id: "user-priya",
    user_name: "Priya Raman",
    message_count: 60,
    tokens_in: 88910,
    tokens_out: 9402,
    web_search_count: 10,
    message_limit_reached: true,
    web_search_limit_reached: true,
  }),
];

/** The Model call log, newest first. */
const modelCallTraces: ModelCallTrace[] = [
  {
    trace_id: "trace-2",
    kind: "message",
    user_id: "user-alex",
    user_name: "Alex Tan",
    user_email: null,
    started_at: "2026-11-17T18:42:00+08:00",
    steps: ["safeguard", "understanding", "reply"],
    tokens_in: 4210,
    tokens_out: 312,
    duration_ms: 3400,
    error_count: 0,
    has_content: false,
  },
  {
    trace_id: "trace-1",
    kind: "check_in",
    user_id: "user-zaf",
    user_name: "Zaf",
    user_email: null,
    started_at: "2026-11-17T09:05:00+08:00",
    steps: ["check_in"],
    tokens_in: 900,
    tokens_out: 60,
    duration_ms: 850,
    error_count: 1,
    has_content: true,
  },
];

/** Builds an Eval Run; fields not shown are plain defaults. */
function evalRun(
  run: Pick<EvalRun, "id" | "state" | "queued_at"> & Partial<EvalRun>,
): EvalRun {
  return {
    started_from: "dashboard",
    started_by_name: "Zaf",
    evals: ["safeguard", "persona"],
    repeats: 1,
    variants: [],
    started_at: run.queued_at,
    finished_at: null,
    case_count: 31,
    case_keys: [],
    cancel_requested: false,
    token_limit: null,
    rerun_of: null,
    passed: 0,
    failed: 0,
    errored: 0,
    tokens_in: 0,
    tokens_out: 0,
    cost_sgd: 0,
    unpriced_models: [],
    ...run,
  };
}

/** The Eval Runs, newest first. */
const evalRuns: EvalRun[] = [
  evalRun({
    id: "run-2",
    state: "running",
    queued_at: "2026-11-17T20:10:00+08:00",
    passed: 12,
    tokens_in: 18000,
    tokens_out: 900,
    cost_sgd: 0.0081,
  }),
  evalRun({
    id: "run-1",
    state: "finished",
    queued_at: "2026-11-16T14:00:00+08:00",
    passed: 29,
    failed: 1,
    errored: 1,
    tokens_in: 40000,
    tokens_out: 2000,
    cost_sgd: 0.0183,
  }),
];

/** Builds an Eval Case; it came from the seed files unless told otherwise. */
function evalCase(key: string, overrides: Partial<EvalCase> = {}): EvalCase {
  return {
    key,
    eval: "safeguard",
    content: {},
    archived: false,
    edited: false,
    updated_at: "2026-11-15T09:00:00+08:00",
    updated_by_name: null,
    ...overrides,
  };
}

/** One Eval's cases. */
const evalCases: EvalCase[] = [
  evalCase("self-harm-hint"),
  evalCase("venting-not-risk", { edited: true, updated_by_name: "Zaf" }),
  evalCase("old-wording", { archived: true }),
];

/**
 * Design fixtures for the AdminCheckInLog (the table template) reference
 * pages, and for the pages built from it. Check-in log values come only
 * from its reference file; the other pages have no reference, so their
 * rows use the people the template draws. Only the issues building this
 * area fill it.
 */
export const adminTablesFixtures: Partial<ApiClient> = {
  listCheckInLog: async () => checkInLog,
  listSafeguardEvents: async () => safeguardEvents,
  listCheckInSchedule: async () => ({
    entries: checkInSchedule,
    total: checkInSchedule.length,
    page: 1,
    page_size: 25,
    now: "2026-11-18T10:00:00+08:00",
  }),
  getUsage: async () => ({
    rows: usageRows,
    daily_message_limit: 60,
    web_search_daily_limit: 10,
  }),
  listModelCallTraces: async () => modelCallTraces,
  listEvalRuns: async () => evalRuns,
  listEvalCases: async (evalName) =>
    evalCases.map((item) => ({ ...item, eval: evalName })),
};
