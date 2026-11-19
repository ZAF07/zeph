"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { DataTable } from "@/components/DataTable";
import { LoadFailed } from "@/components/LoadFailed";
import { SelectFilter } from "@/components/SelectFilter";
import { type StatTile, StatTiles } from "@/components/StatTiles";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import type { DailyUsage } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import {
  formatFullCount,
  formatUsageCount,
  limitsReached,
  summarizeUsage,
  usageCsv,
} from "@/lib/usage";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const periods = [
  { value: "1", label: "Today" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
];

const columns: TableColumn<DailyUsage>[] = [
  {
    heading: "Date",
    isMain: true,
    cell: (row) => (
      <span className="whitespace-nowrap">
        {formatShortDay(row.day, "UTC")}
      </span>
    ),
  },
  {
    heading: "User",
    isMain: true,
    cell: (row) => row.user_name ?? row.user_email ?? "Unknown User",
  },
  { heading: "Messages", cell: (row) => formatFullCount(row.message_count) },
  { heading: "Tokens in", cell: (row) => formatFullCount(row.tokens_in) },
  { heading: "Tokens out", cell: (row) => formatFullCount(row.tokens_out) },
  {
    heading: "Web searches",
    cell: (row) => formatFullCount(row.web_search_count),
  },
  {
    heading: "Limits",
    cell: (row) => {
      const reached = limitsReached(row);
      if (reached.length === 0) {
        return "—";
      }
      return (
        <span className="inline-flex flex-wrap justify-end gap-1.5">
          {reached.map((note) => (
            <StatusPill key={note} filled={false}>
              {note}
            </StatusPill>
          ))}
        </span>
      );
    },
  },
];

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
 * Works out the totals above the usage table.
 *
 * @param rows - The usage rows in the period.
 * @param periodLabel - The period in lower case, like "today".
 * @returns The four totals.
 */
function totalsOf(rows: DailyUsage[], periodLabel: string): StatTile[] {
  const summary = summarizeUsage(rows);
  return [
    { label: "Tokens in", value: summary.tokensIn },
    { label: "Tokens out", value: summary.tokensOut },
    { label: "Messages", value: summary.messages },
    { label: "Web searches", value: summary.webSearches },
  ].map((total) => ({
    label: `${total.label} · ${periodLabel}`,
    value: formatUsageCount(total.value),
  }));
}

/**
 * The admin Usage page's body: tokens, messages and web searches per User per
 * day for a chosen period, with totals and a CSV download. Counts only, never
 * message content. Built from the admin table template.
 *
 * @returns The totals, filters and table, or a loading, empty or error state
 *   in place of the table.
 */
export function AdminUsage() {
  const apiClient = useApiClient();
  const [period, setPeriod] = useState("1");
  const days = Number(period);
  const usageQuery = useQuery({
    queryKey: queryKeys.usage(days),
    queryFn: () => apiClient.getUsage(days),
  });
  const report = usageQuery.data;
  const rows = report?.rows ?? [];
  const periodLabel = (
    periods.find((option) => option.value === period)?.label ?? ""
  ).toLowerCase();

  return (
    <>
      {report ? <StatTiles tiles={totalsOf(rows, periodLabel)} /> : null}

      <div className="flex flex-wrap items-center gap-2.5">
        <SelectFilter
          label="Period"
          options={periods}
          value={period}
          onChange={setPeriod}
        />
        <button
          type="button"
          className={secondaryButton}
          disabled={rows.length === 0}
          onClick={() => downloadCsv(rows, days)}
        >
          Download CSV
        </button>
      </div>

      {usageQuery.isPending ? <TableLoading label="Loading usage" /> : null}

      {!report && usageQuery.isError ? (
        <LoadFailed
          title="Couldn’t load usage"
          body="Usage is still being recorded as normal."
          onRetry={() => void usageQuery.refetch()}
        />
      ) : null}

      {report && rows.length === 0 ? (
        <TableEmpty
          title="No usage yet"
          body="Rows appear once Users message Zeph. You’ll see counts per User per day — never message content."
        />
      ) : null}

      {rows.length > 0 ? (
        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(row) => `${row.day}-${row.user_id}`}
          noMessageContent
          minWidthClass="min-w-[820px]"
        />
      ) : null}
    </>
  );
}
