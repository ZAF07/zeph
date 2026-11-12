import type { DailyUsage } from "@/lib/api-client";

/** The totals shown above the usage table. */
export type UsageSummary = {
  tokensIn: number;
  tokensOut: number;
  messages: number;
  webSearches: number;
};

const csvHeadings = [
  "Date",
  "User",
  "Email",
  "Messages",
  "Tokens in",
  "Tokens out",
  "Web searches",
];

const compactNumber = new Intl.NumberFormat("en", {
  notation: "compact",
  maximumSignificantDigits: 3,
});

const fullNumber = new Intl.NumberFormat("en");

/**
 * Adds up tokens, messages and web searches over the usage rows.
 *
 * @param rows - The usage rows in the period.
 * @returns The totals.
 */
export function summarizeUsage(rows: DailyUsage[]): UsageSummary {
  return rows.reduce(
    (summary, row) => ({
      tokensIn: summary.tokensIn + row.tokens_in,
      tokensOut: summary.tokensOut + row.tokens_out,
      messages: summary.messages + row.message_count,
      webSearches: summary.webSearches + row.web_search_count,
    }),
    { tokensIn: 0, tokensOut: 0, messages: 0, webSearches: 0 },
  );
}

/**
 * Writes a total the way the usage cards show it: big counts short.
 *
 * @param count - The count.
 * @returns "1.84M" or "212K" from ten thousand up, else "1,406".
 */
export function formatUsageCount(count: number): string {
  return count < 10_000
    ? fullNumber.format(count)
    : compactNumber.format(count);
}

/**
 * Writes a count in full, like "31,240".
 *
 * @param count - The count.
 * @returns The count with thousands separators.
 */
export function formatFullCount(count: number): string {
  return fullNumber.format(count);
}

/**
 * Says which daily limits turned something away for a User on a day.
 *
 * @param row - The User's usage on that day.
 * @returns "Message limit reached" and/or "Search limit reached"; none if
 *   neither limit was hit.
 */
export function limitsReached(row: DailyUsage): string[] {
  const reached: string[] = [];
  if (row.message_limit_reached) {
    reached.push("Message limit reached");
  }
  if (row.web_search_limit_reached) {
    reached.push("Search limit reached");
  }
  return reached;
}

/**
 * Puts one CSV value in quotes when it holds a comma, quote or line break.
 *
 * @param value - The value.
 * @returns The value, ready for a CSV line.
 */
function csvValue(value: string | number): string {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/**
 * Writes the usage rows as CSV, one line per User per day.
 *
 * @param rows - The usage rows.
 * @returns The CSV text with a heading line.
 */
export function usageCsv(rows: DailyUsage[]): string {
  const lines = rows.map((row) =>
    [
      row.day,
      row.user_name ?? "",
      row.user_email ?? "",
      row.message_count,
      row.tokens_in,
      row.tokens_out,
      row.web_search_count,
    ]
      .map(csvValue)
      .join(","),
  );
  return [csvHeadings.join(","), ...lines].join("\n");
}
