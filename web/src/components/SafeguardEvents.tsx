"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataTable } from "@/components/DataTable";
import { FilterPills } from "@/components/FilterPills";
import { LoadFailed } from "@/components/LoadFailed";
import { SelectFilter } from "@/components/SelectFilter";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import { TableNoMatches } from "@/components/TableNoMatches";
import type {
  RiskType,
  SafeguardEvent,
  SafeguardEventFilter,
} from "@/lib/api-client";
import { countryName } from "@/lib/countries";
import { formatSavedAt } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { riskTypeLabel, riskTypes } from "@/lib/risk-types";
import { useApiClient } from "@/lib/use-api-client";

type RiskFilter = RiskType | "all";

const periods = [
  { value: "30", label: "Last 30 days" },
  { value: "7", label: "Last 7 days" },
  { value: "all", label: "All time" },
];

const riskFilters: { id: RiskFilter; label: string }[] = [
  { id: "all", label: "All" },
  ...riskTypes,
];

const columns: TableColumn<SafeguardEvent>[] = [
  {
    heading: "User",
    isMain: true,
    cell: (event) => (
      <Link href="/admin/users" className="text-text underline">
        {event.user_name ?? event.user_email ?? "Unknown User"}
      </Link>
    ),
  },
  {
    heading: "Time",
    isMain: true,
    cell: (event) => (
      <span className="whitespace-nowrap">
        {formatSavedAt(event.created_at)}
      </span>
    ),
  },
  {
    heading: "Risk type",
    cell: (event) => (
      <StatusPill filled={false} danger>
        {riskTypeLabel(event.risk_type)}
      </StatusPill>
    ),
  },
  { heading: "Crisis Reply", cell: () => "Sent" },
  {
    heading: "Helplines shown",
    cell: (event) =>
      event.helplines_country
        ? countryName(event.helplines_country)
        : "International fallback",
  },
];

/**
 * The admin Safeguard Events page: each time the Safeguard detected risk and
 * sent the Crisis Reply. Who and when only, never what was said. Built from
 * the admin table template.
 *
 * @returns The filters and table, or a loading, no-match, empty or error
 *   state in place of the table.
 */
export function SafeguardEvents() {
  const apiClient = useApiClient();
  const [riskType, setRiskType] = useState<RiskFilter>("all");
  const [period, setPeriod] = useState("30");

  const filter: SafeguardEventFilter = {
    riskType: riskType === "all" ? undefined : riskType,
    days: period === "all" ? undefined : Number(period),
  };
  const eventsQuery = useQuery({
    queryKey: queryKeys.safeguardEvents(filter),
    queryFn: () => apiClient.listSafeguardEvents(filter),
  });
  const events = eventsQuery.data;

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <FilterPills
          label="Risk type"
          options={riskFilters}
          chosen={riskType}
          onChoose={setRiskType}
        />
        <SelectFilter
          label="Period"
          options={periods}
          value={period}
          onChange={setPeriod}
        />
      </div>

      {eventsQuery.isPending ? <TableLoading label="Loading events" /> : null}

      {!events && eventsQuery.isError ? (
        <LoadFailed
          title="Couldn’t load Safeguard Events"
          body="Safeguard itself is unaffected and still screening messages."
          onRetry={() => void eventsQuery.refetch()}
        />
      ) : null}

      {events && events.length === 0 && riskType !== "all" ? (
        <TableNoMatches />
      ) : null}

      {events && events.length === 0 && riskType === "all" ? (
        <TableEmpty
          title="No Safeguard Events in this period"
          body="When Safeguard detects risk you’ll see the User, the time and the risk type here. Message content is never stored for Admins, so it will never appear."
        />
      ) : null}

      {events && events.length > 0 ? (
        <DataTable
          columns={columns}
          rows={events}
          rowKey={(event) => event.id}
          noMessageContent
          minWidthClass="min-w-[760px]"
        />
      ) : null}
    </>
  );
}
