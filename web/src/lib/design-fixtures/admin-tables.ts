import type { ApiClient, CheckInLogEntry } from "@/lib/api-client";

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
 * Design fixtures for the AdminCheckInLog (the table template) reference
 * pages. Values come only from those reference files. Only the issue
 * building this area fills it.
 */
export const adminTablesFixtures: Partial<ApiClient> = {
  listCheckInLog: async () => checkInLog,
};
