import type { CheckInLogEntry } from "@/lib/api-client";

/** Which decisions the Check-in log shows. */
export type CheckInLogOutcomeFilter = "all" | "sent" | "skipped";

/** The totals shown above the Check-in log. */
export type CheckInLogSummary = {
  sent: number;
  skipped: number;
  repliedPercent: number | null;
  pausedByIgnoreRule: number;
};

/**
 * Adds up the Check-in log: sends, skips, the share of answered sends that
 * were replied to, and how often the ignore rule paused a User.
 *
 * @param entries - The decisions in the period.
 * @returns The totals; `repliedPercent` is null while no send can be judged.
 */
export function summarizeCheckInLog(
  entries: CheckInLogEntry[],
): CheckInLogSummary {
  const sends = entries.filter((entry) => entry.outcome === "sent");
  const judged = sends.filter((entry) => entry.status !== "sent");
  const replied = judged.filter((entry) => entry.status === "replied");
  return {
    sent: sends.length,
    skipped: entries.filter((entry) => entry.outcome === "skipped").length,
    repliedPercent:
      judged.length === 0
        ? null
        : Math.round((replied.length / judged.length) * 100),
    pausedByIgnoreRule: entries.filter(
      (entry) => entry.outcome === "asked_about_fewer",
    ).length,
  };
}

/**
 * Keeps the Check-in log entries that match an outcome and a User search.
 *
 * @param entries - The decisions in the period.
 * @param outcome - All, only sends, or only skips.
 * @param userQuery - Text to find in the User's name or email; "" for all.
 * @returns The matching entries, in the same order.
 */
export function filterCheckInLog(
  entries: CheckInLogEntry[],
  outcome: CheckInLogOutcomeFilter,
  userQuery: string,
): CheckInLogEntry[] {
  const query = userQuery.trim().toLowerCase();
  return entries.filter((entry) => {
    if (outcome !== "all" && entry.outcome !== outcome) {
      return false;
    }
    const who = `${entry.user_name ?? ""} ${entry.user_email ?? ""}`;
    return who.toLowerCase().includes(query);
  });
}
