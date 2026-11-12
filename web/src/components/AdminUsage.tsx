"use client";

import { useCallback, useEffect, useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import type { DailyUsage, UsageReport } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import {
  formatFullCount,
  formatUsageCount,
  limitsReached,
  summarizeUsage,
  usageCsv,
} from "@/lib/usage";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; report: UsageReport };

const periods = [
  { days: 1, label: "Today" },
  { days: 7, label: "Last 7 days" },
  { days: 30, label: "Last 30 days" },
];

const headings = [
  "Date",
  "User",
  "Messages",
  "Tokens in",
  "Tokens out",
  "Web searches",
  "Limits",
];

const cell = "px-[18px] py-3.5";
const numberCell = `${cell} text-right tabular-nums`;

/**
 * Hands the browser a CSV file of the usage rows to save.
 *
 * @param rows - The usage rows.
 * @param days - How many days they cover, used in the file name.
 */
function downloadCsv(rows: DailyUsage[], days: number) {
  const url = URL.createObjectURL(
    new Blob([usageCsv(rows)], { type: "text/csv" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download =
    days === 1 ? "usage-today.csv" : `usage-last-${days}-days.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

/**
 * The admin Usage page's body: tokens, messages and web searches per User per
 * day for a chosen period, with totals and a CSV download. Counts only, never
 * message content.
 *
 * @returns The controls, totals and table, or a loading, empty or error state.
 */
export function AdminUsage() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [days, setDays] = useState(1);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({ kind: "loaded", report: await apiClient.getUsage(days) });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient, days]);

  useEffect(() => {
    void load();
  }, [load]);

  const rows = state.kind === "loaded" ? state.report.rows : [];
  const periodLabel = (
    periods.find((option) => option.days === days)?.label ?? ""
  ).toLowerCase();
  const summary = summarizeUsage(rows);
  const totals = [
    { label: "Tokens in", value: summary.tokensIn },
    { label: "Tokens out", value: summary.tokensOut },
    { label: "Messages", value: summary.messages },
    { label: "Web searches", value: summary.webSearches },
  ];

  return (
    <>
      <div className="flex flex-wrap items-center justify-end gap-2.5">
        <label className="flex-[1_1_200px] sm:flex-none">
          <span className="sr-only">Period</span>
          <select
            className={`${inputField} min-h-10 py-2 sm:w-[220px]`}
            value={days}
            onChange={(event) => setDays(Number(event.target.value))}
          >
            {periods.map((option) => (
              <option key={option.days} value={option.days}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className={`${secondaryButton} flex-[1_1_200px] sm:flex-none`}
          disabled={rows.length === 0}
          onClick={() => downloadCsv(rows, days)}
        >
          Download CSV
        </button>
      </div>

      {state.kind === "loading" ? (
        <div
          aria-busy="true"
          aria-label="Loading usage"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {state.kind === "failed" ? (
        <LoadFailed
          title="Couldn’t load usage"
          body="Usage is still being recorded as normal."
          onRetry={() => void load()}
        />
      ) : null}

      {state.kind === "loaded" ? (
        <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(min(180px,100%),1fr))] gap-3">
          {totals.map((total) => (
            <div
              key={total.label}
              className="flex flex-col gap-0.5 rounded-card border border-line bg-white px-[18px] py-4"
            >
              <dt className="text-caption text-ink-muted">
                {total.label} · {periodLabel}
              </dt>
              <dd className="m-0 text-[30px] font-normal">
                {formatUsageCount(total.value)}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}

      {state.kind === "loaded" && rows.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No usage yet
          </span>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            Rows appear once Users message Zeph. You’ll see counts per User per
            day — never message content.
          </p>
        </div>
      ) : null}

      {state.kind === "loaded" && rows.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="w-full min-w-[820px] border-collapse text-sm">
            <caption className="border-b border-line px-4 py-2.5 text-left">
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                <LockIcon />
                No message content · daily limit{" "}
                {state.report.daily_message_limit} messages,{" "}
                {state.report.web_search_daily_limit} web searches
              </span>
            </caption>
            <thead>
              <tr>
                {headings.map((heading, index) => (
                  <th
                    key={heading}
                    scope="col"
                    className={`whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted ${
                      index >= 2 && index <= 5 ? "text-right" : "text-left"
                    }`}
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const reached = limitsReached(row);
                return (
                  <tr
                    key={`${row.day}-${row.user_id}`}
                    className="border-b border-line last:border-b-0"
                  >
                    <td className={`${cell} whitespace-nowrap`}>
                      {formatShortDay(row.day, "UTC")}
                    </td>
                    <td className={cell}>
                      {row.user_name ?? row.user_email ?? "Unknown User"}
                    </td>
                    <td className={numberCell}>
                      {formatFullCount(row.message_count)}
                    </td>
                    <td className={numberCell}>
                      {formatFullCount(row.tokens_in)}
                    </td>
                    <td className={numberCell}>
                      {formatFullCount(row.tokens_out)}
                    </td>
                    <td className={numberCell}>
                      {formatFullCount(row.web_search_count)}
                    </td>
                    <td className={cell}>
                      {reached.length === 0 ? (
                        "—"
                      ) : (
                        <span className="flex flex-wrap gap-1.5">
                          {reached.map((note) => (
                            <span
                              key={note}
                              className="inline-flex items-center whitespace-nowrap rounded-full bg-yellow-tint px-2.5 py-[3px] text-xs font-medium text-yellow-deep"
                            >
                              {note}
                            </span>
                          ))}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}

      <p className="m-0 text-caption text-ink-muted">
        Tokens include Safeguard, response composition, post-conversation
        processing and Check-ins.
      </p>
    </>
  );
}
