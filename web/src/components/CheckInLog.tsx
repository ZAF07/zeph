"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataTable } from "@/components/DataTable";
import { FilterPills } from "@/components/FilterPills";
import { LoadFailed } from "@/components/LoadFailed";
import { SearchField } from "@/components/SearchField";
import { SelectFilter } from "@/components/SelectFilter";
import { type StatTile, StatTiles } from "@/components/StatTiles";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import { TableNoMatches } from "@/components/TableNoMatches";
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
import { formatLoggedAt } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const periods = [
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
];

const outcomeFilters: { id: CheckInLogOutcomeFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "sent", label: "Sent" },
  { id: "skipped", label: "Skipped" },
];

const outcomeLabels: Record<CheckInOutcome, string> = {
  sent: "Sent",
  skipped: "Skipped",
  asked_about_fewer: "Paused",
};

const replyLabels: Record<CheckInStatus, string> = {
  sent: "Waiting",
  replied: "Replied",
  no_reply: "No reply",
  skipped: "—",
};

/**
 * Says what the Check-in log shows in an entry's skip reason column.
 *
 * @param entry - The decision.
 * @returns The skip reason, the ignore rule note, or a dash.
 */
function reasonText(entry: CheckInLogEntry): string {
  if (entry.outcome === "asked_about_fewer") {
    return "Three in a row went unanswered";
  }
  return entry.skip_reason ?? "—";
}

/**
 * Works out the totals above the Check-in log.
 *
 * @param entries - The decisions in the period.
 * @returns The four totals, in the drawn order.
 */
function totalsOf(entries: CheckInLogEntry[]): StatTile[] {
  const summary = summarizeCheckInLog(entries);
  return [
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
}

const columns: TableColumn<CheckInLogEntry>[] = [
  {
    heading: "Time",
    isMain: true,
    cell: (entry) => formatLoggedAt(entry.decided_at),
  },
  {
    heading: "User",
    isMain: true,
    cell: (entry) => entry.user_name ?? entry.user_email ?? "Unknown User",
  },
  {
    heading: "Outcome",
    cell: (entry) => (
      <span className="inline-flex flex-col items-start gap-[3px]">
        <StatusPill filled={entry.outcome === "sent"}>
          {outcomeLabels[entry.outcome]}
        </StatusPill>
        {entry.requested_by ? (
          <span className="text-[12px] text-soft">
            Asked for by {entry.requested_by}
          </span>
        ) : null}
        {entry.woven_in ? (
          <span className="text-[12px] text-soft">Woven in</span>
        ) : null}
      </span>
    ),
  },
  { heading: "Check-in Kind", cell: (entry) => entry.kind ?? "—" },
  { heading: "Skip reason", cell: reasonText },
  { heading: "Reply", cell: (entry) => replyLabels[entry.status] },
];

/**
 * The admin Check-in log: every decision the Check-ins service made — sent,
 * woven into a reply or not, skipped and why, or paused by the ignore rule —
 * with totals, and which Admin asked for one with Check in Now. Never the
 * message text. Built from the admin table template.
 *
 * @returns The totals, filters and table, or a loading, no-match, empty or
 *   error state in place of the table.
 */
export function CheckInLog() {
  const apiClient = useApiClient();
  const [days, setDays] = useState("7");
  const [outcome, setOutcome] = useState<CheckInLogOutcomeFilter>("all");
  const [userQuery, setUserQuery] = useState("");

  const logQuery = useQuery({
    queryKey: queryKeys.checkInLog(Number(days)),
    queryFn: () => apiClient.listCheckInLog(Number(days)),
  });
  const entries = logQuery.data;
  const shown = entries ? filterCheckInLog(entries, outcome, userQuery) : [];

  return (
    <>
      {entries ? <StatTiles tiles={totalsOf(entries)} /> : null}

      <div className="flex flex-wrap items-center gap-2.5">
        <SearchField
          label="Filter by user"
          placeholder="Filter by user"
          value={userQuery}
          onChange={setUserQuery}
        />
        <FilterPills
          label="Outcome"
          options={outcomeFilters}
          chosen={outcome}
          onChoose={setOutcome}
        />
        <SelectFilter
          label="Period"
          options={periods}
          value={days}
          onChange={setDays}
        />
      </div>

      {logQuery.isPending ? <TableLoading label="Loading log" /> : null}

      {!entries && logQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Check-in log"
          body="Check your connection and try again."
          onRetry={() => void logQuery.refetch()}
        />
      ) : null}

      {entries && entries.length === 0 ? (
        <TableEmpty
          title="No check-ins yet"
          body="Entries appear once users turn check-ins on."
        />
      ) : null}

      {entries && entries.length > 0 && shown.length === 0 ? (
        <TableNoMatches />
      ) : null}

      {shown.length > 0 ? (
        <DataTable
          columns={columns}
          rows={shown}
          rowKey={(entry) => entry.id}
          noMessageContent
          minWidthClass="min-w-[820px]"
        />
      ) : null}
    </>
  );
}
