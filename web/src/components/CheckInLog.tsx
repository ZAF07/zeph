"use client";

import { useCallback, useEffect, useState } from "react";

import { inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import type {
  CheckInLogEntry,
  CheckInOutcome,
  CheckInStatus,
} from "@/lib/api-client";
import {
  type CheckInLogOutcomeFilter,
  filterCheckInLog,
  summarizeCheckInLog,
} from "@/lib/check-in-log";
import { formatSavedAt } from "@/lib/dates";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; entries: CheckInLogEntry[] };

const periods = [
  { days: 7, label: "Last 7 days" },
  { days: 30, label: "Last 30 days" },
];

const outcomeFilters: { id: CheckInLogOutcomeFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "sent", label: "Sent" },
  { id: "skipped", label: "Skipped" },
];

const outcomePills: Record<CheckInOutcome, { label: string; pill: string }> = {
  sent: { label: "Sent", pill: "bg-blue-tint text-blue-deep" },
  skipped: { label: "Skipped", pill: "bg-code text-ink-body" },
  asked_about_fewer: {
    label: "Paused",
    pill: "bg-yellow-tint text-yellow-deep",
  },
};

const replyLabels: Record<CheckInStatus, string> = {
  sent: "Waiting",
  replied: "Replied",
  no_reply: "No reply",
  skipped: "—",
};

const headings = [
  "Time",
  "User",
  "Outcome",
  "Check-in Kind",
  "Skip reason",
  "Reply",
];

const cell = "px-[18px] py-3.5";

/**
 * Says what the Check-in log shows in an entry's skip reason column.
 *
 * @param entry - The decision.
 * @returns The skip reason, the ignore rule note, or a dash.
 */
function reasonText(entry: CheckInLogEntry): string {
  if (entry.outcome === "asked_about_fewer") {
    return "Ignore threshold reached — asked once about fewer";
  }
  return entry.skip_reason ?? "—";
}

/**
 * The admin Check-in log: every decision the Check-ins service made — sent,
 * skipped and why, or paused by the ignore rule — with totals. Never the
 * message text.
 *
 * @returns The filters, totals and table, or a loading, empty or error state.
 */
export function CheckInLog() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [days, setDays] = useState(7);
  const [outcome, setOutcome] = useState<CheckInLogOutcomeFilter>("all");
  const [userQuery, setUserQuery] = useState("");

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({
        kind: "loaded",
        entries: await apiClient.listCheckInLog(days),
      });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient, days]);

  useEffect(() => {
    void load();
  }, [load]);

  const entries = state.kind === "loaded" ? state.entries : [];
  const summary = summarizeCheckInLog(entries);
  const shown = filterCheckInLog(entries, outcome, userQuery);
  const totals = [
    { label: "Sent", value: String(summary.sent) },
    { label: "Skipped", value: String(summary.skipped) },
    {
      label: "Replied to",
      value:
        summary.repliedPercent === null ? "—" : `${summary.repliedPercent}%`,
    },
    {
      label: "Paused by ignore rule",
      value: String(summary.pausedByIgnoreRule),
    },
  ];

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <label className="flex-[1_1_240px]">
          <span className="sr-only">Filter by user</span>
          <input
            type="search"
            className={`${inputField} min-h-10 py-2`}
            placeholder="Filter by user"
            value={userQuery}
            onChange={(event) => setUserQuery(event.target.value)}
          />
        </label>
        <div
          role="group"
          aria-label="Outcome"
          className="flex flex-wrap gap-1.5"
        >
          {outcomeFilters.map((option) => (
            <button
              key={option.id}
              type="button"
              aria-pressed={outcome === option.id}
              onClick={() => setOutcome(option.id)}
              className={`min-h-10 cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium ${
                outcome === option.id
                  ? "border-ink bg-ink text-white"
                  : "border-line-strong bg-transparent text-ink-body"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <label>
          <span className="sr-only">Period</span>
          <select
            className={`${inputField} min-h-10 w-auto py-2`}
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
      </div>

      {state.kind === "loading" ? (
        <div
          aria-busy="true"
          aria-label="Loading log"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {state.kind === "failed" ? (
        <LoadFailed
          title="Couldn’t load the Check-in log"
          body="Check-ins are still being scheduled as normal."
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
              <dt className="text-caption text-ink-muted">{total.label}</dt>
              <dd className="m-0 text-[30px] font-normal">{total.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      {state.kind === "loaded" && entries.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No Check-in decisions yet
          </span>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            Entries appear once Users turn Check-ins on. You’ll see the Kind or
            skip reason per User — never the message text.
          </p>
        </div>
      ) : null}

      {state.kind === "loaded" && entries.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="w-full min-w-[820px] border-collapse text-sm">
            <caption className="border-b border-line px-4 py-2.5 text-left">
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                <LockIcon />
                No message content
              </span>
            </caption>
            <thead>
              <tr>
                {headings.map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className="whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 text-left font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {shown.map((entry) => {
                const pill = outcomePills[entry.outcome];
                return (
                  <tr
                    key={entry.id}
                    className="border-b border-line last:border-b-0"
                  >
                    <td className={`${cell} whitespace-nowrap`}>
                      {formatSavedAt(entry.decided_at)}
                    </td>
                    <td className={cell}>
                      {entry.user_name ?? entry.user_email ?? "Unknown User"}
                    </td>
                    <td className={cell}>
                      <span
                        className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium ${pill.pill}`}
                      >
                        {pill.label}
                      </span>
                    </td>
                    <td className={cell}>{entry.kind ?? "—"}</td>
                    <td className={cell}>{reasonText(entry)}</td>
                    <td className={`${cell} whitespace-nowrap`}>
                      {replyLabels[entry.status]}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {shown.length === 0 ? (
            <p className="m-0 px-[18px] py-4 text-caption text-ink-muted">
              Nothing matches these filters.
            </p>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
