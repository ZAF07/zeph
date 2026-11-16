import type {
  CheckInScheduleEntry,
  CheckInSchedulePage,
} from "@/lib/api-client";

/**
 * Builds one Check-in Schedule row for tests: Ren in Singapore, due in 3
 * hours, on most days, not paused or held back.
 *
 * @param overrides - Fields to swap out.
 * @returns The row.
 */
export function scheduleEntry(
  overrides: Partial<CheckInScheduleEntry> = {},
): CheckInScheduleEntry {
  return {
    user_id: "ren",
    name: "Ren Okafor",
    email: "ren@example.com",
    time_zone: "Asia/Singapore",
    next_due_at: "2026-11-17T05:00:00Z",
    frequency: "most_days",
    quiet_hours_start: "22:00:00",
    quiet_hours_end: "07:30:00",
    paused: false,
    paused_until: null,
    check_ins_work: true,
    held_back: null,
    changed_by_admin: [],
    ...overrides,
  };
}

/**
 * Builds one page of the Check-in Schedule for tests, read at 02:00 UTC.
 *
 * @param entries - The rows on the page.
 * @param overrides - Fields to swap out.
 * @returns The page.
 */
export function schedulePage(
  entries: CheckInScheduleEntry[],
  overrides: Partial<CheckInSchedulePage> = {},
): CheckInSchedulePage {
  return {
    entries,
    total: entries.length,
    page: 1,
    page_size: 25,
    now: "2026-11-17T02:00:00Z",
    ...overrides,
  };
}
