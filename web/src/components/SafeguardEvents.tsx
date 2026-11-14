"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import type { RiskType, SafeguardEventFilter } from "@/lib/api-client";
import { countryName } from "@/lib/countries";
import { formatSavedAt } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { riskTypeLabel, riskTypes } from "@/lib/risk-types";
import { useApiClient } from "@/lib/use-api-client";

const periods: { value: string; label: string; phrase: string }[] = [
  { value: "30", label: "Last 30 days", phrase: "in the last 30 days" },
  { value: "7", label: "Last 7 days", phrase: "in the last 7 days" },
  { value: "all", label: "All time", phrase: "in total" },
];

const headings = [
  "User",
  "Time",
  "Risk type",
  "Crisis Reply",
  "Helplines shown",
];

/**
 * The admin Safeguard Events page: each time the Safeguard detected risk and
 * sent the Crisis Reply. Who and when only, never what was said.
 *
 * @returns The filters and table, or a loading, empty or error state.
 */
export function SafeguardEvents() {
  const apiClient = useApiClient();
  const [riskType, setRiskType] = useState<RiskType | null>(null);
  const [period, setPeriod] = useState("30");
  const periodPhrase =
    periods.find((option) => option.value === period)?.phrase ?? "";

  const filter: SafeguardEventFilter = {
    riskType: riskType ?? undefined,
    days: period === "all" ? undefined : Number(period),
  };
  const eventsQuery = useQuery({
    queryKey: queryKeys.safeguardEvents(filter),
    queryFn: () => apiClient.listSafeguardEvents(filter),
  });
  const events = eventsQuery.data;

  const riskFilters: { id: RiskType | null; label: string }[] = [
    { id: null, label: "All" },
    ...riskTypes,
  ];

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div
          role="group"
          aria-label="Risk type"
          className="flex flex-wrap gap-1.5"
        >
          {riskFilters.map((option) => (
            <button
              key={option.label}
              type="button"
              aria-pressed={riskType === option.id}
              onClick={() => setRiskType(option.id)}
              className={`min-h-10 cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium ${
                riskType === option.id
                  ? "border-ink bg-ink text-white"
                  : "border-line-strong bg-transparent text-ink-body"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="flex flex-col gap-1 text-caption text-ink-muted">
          <label htmlFor="safeguard-event-period">Period</label>
          <select
            id="safeguard-event-period"
            className={`${inputField} min-h-10 w-auto py-2`}
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
          >
            {periods.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {eventsQuery.isPending ? (
        <div
          aria-busy="true"
          aria-label="Loading events"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {!events && eventsQuery.isError ? (
        <LoadFailed
          title="Couldn’t load Safeguard Events"
          body="Safeguard itself is unaffected and still screening messages."
          onRetry={() => void eventsQuery.refetch()}
        />
      ) : null}

      {events && events.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No Safeguard Events in this period
          </span>
          <p className="m-0 max-w-[36em] text-caption text-ink-muted">
            When Safeguard detects risk you’ll see the User, the time and the
            risk type here. Message content is never stored for Admins, so it
            will never appear.
          </p>
        </div>
      ) : null}

      {events && events.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border border-line bg-white">
            <table className="w-full min-w-[760px] border-collapse text-sm">
              <caption className="border-b border-line px-4 py-2.5 text-left">
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                  <LockIcon />
                  No message content · {events.length}{" "}
                  {events.length === 1 ? "event" : "events"} {periodPhrase}
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
                {events.map((event) => (
                  <tr
                    key={event.id}
                    className="border-b border-line last:border-b-0"
                  >
                    <td className="px-[18px] py-3.5">
                      <Link href="/admin/users" className="font-medium">
                        {event.user_name ?? event.user_email ?? "Unknown User"}
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-[18px] py-3.5">
                      {formatSavedAt(event.created_at)}
                    </td>
                    <td className="px-[18px] py-3.5">
                      <span className="inline-flex items-center whitespace-nowrap rounded-full bg-danger-tint px-2.5 py-[3px] text-xs font-medium text-danger-deep">
                        {riskTypeLabel(event.risk_type)}
                      </span>
                    </td>
                    <td className="px-[18px] py-3.5">Sent</td>
                    <td className="px-[18px] py-3.5">
                      {event.helplines_country
                        ? countryName(event.helplines_country)
                        : "International fallback"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="m-0 text-caption text-ink-muted">
            “International fallback” means the User’s country had no Helplines —
            add them in <Link href="/admin/safety">Safety</Link>.
          </p>
        </>
      ) : null}
    </>
  );
}
