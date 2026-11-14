"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import type { ModelCallTraceFilter, ModelStep } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import {
  describeSteps,
  formatDuration,
  modelSteps,
  traceKindLabel,
} from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const periods = [
  { days: 1, label: "Last 24 hours" },
  { days: 7, label: "Last 7 days" },
  { days: 30, label: "Last 30 days" },
];

const headings = [
  "Time",
  "User",
  "For",
  "Steps",
  "Tokens",
  "Time taken",
  "Errors",
  "Content",
];

const cell = "px-[18px] py-3.5";

const numberFormat = new Intl.NumberFormat("en");

/**
 * The admin Model Call Log: one trace per Message, Check-in or Conversation
 * end, newest first, filtered by User, step, period and errors. Each trace
 * opens on its own page. Content is only ever there for Admins' own chats
 * and Evals.
 *
 * @returns The filters and table, or a loading, empty or error state.
 */
export function ModelCallLog() {
  const apiClient = useApiClient();
  const [userId, setUserId] = useState("");
  const [step, setStep] = useState<ModelStep | "">("");
  const [days, setDays] = useState(7);
  const [errorsOnly, setErrorsOnly] = useState(false);

  const filter: ModelCallTraceFilter = {
    days,
    ...(userId ? { userId } : {}),
    ...(step ? { step } : {}),
    ...(errorsOnly ? { errorsOnly } : {}),
  };
  const tracesQuery = useQuery({
    queryKey: queryKeys.modelCallTraces(filter),
    queryFn: () => apiClient.listModelCallTraces(filter),
  });
  const usersQuery = useQuery({
    queryKey: queryKeys.adminUsers,
    queryFn: () => apiClient.listAdminUsers(),
  });
  const traces = tracesQuery.data;

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <label>
          <span className="sr-only">User</span>
          <select
            className={`${inputField} min-h-10 w-auto py-2`}
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
          >
            <option value="">All Users</option>
            {(usersQuery.data ?? []).map((user) => (
              <option key={user.id} value={user.id}>
                {user.name ?? user.email ?? "Unknown User"}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="sr-only">Step</span>
          <select
            className={`${inputField} min-h-10 w-auto py-2`}
            value={step}
            onChange={(event) =>
              setStep(
                modelSteps.find((option) => option.id === event.target.value)
                  ?.id ?? "",
              )
            }
          >
            <option value="">All steps</option>
            {modelSteps.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
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
        <button
          type="button"
          aria-pressed={errorsOnly}
          onClick={() => setErrorsOnly(!errorsOnly)}
          className={`min-h-10 cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium ${
            errorsOnly
              ? "border-ink bg-ink text-white"
              : "border-line-strong bg-transparent text-ink-body"
          }`}
        >
          Errors only
        </button>
      </div>

      {tracesQuery.isPending ? (
        <div
          aria-busy="true"
          aria-label="Loading log"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {traces === undefined && tracesQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Model Call Log"
          body="The Companion is still replying as normal."
          onRetry={() => void tracesQuery.refetch()}
        />
      ) : null}

      {traces !== undefined && traces.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No model calls yet
          </span>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            Traces appear as the Companion answers Messages, sends Check-ins and
            wraps up Conversations. Nothing matches these filters yet.
          </p>
        </div>
      ) : null}

      {traces !== undefined && traces.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="w-full min-w-[920px] border-collapse text-sm">
            <caption className="border-b border-line px-4 py-2.5 text-left">
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                <LockIcon />
                Content only for Admins’ own chats and Evals
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
              {traces.map((trace) => (
                <tr
                  key={trace.trace_id}
                  className="border-b border-line last:border-b-0"
                >
                  <td className={`${cell} whitespace-nowrap`}>
                    <Link
                      href={`/admin/model-calls/${trace.trace_id}`}
                      className="font-medium"
                    >
                      {formatSavedAt(trace.started_at)}
                    </Link>
                  </td>
                  <td className={cell}>
                    {trace.user_name ?? trace.user_email ?? "Unknown User"}
                  </td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {traceKindLabel(trace.kind)}
                  </td>
                  <td className={cell}>{describeSteps(trace.steps)}</td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {`${numberFormat.format(trace.tokens_in)} in / ${numberFormat.format(trace.tokens_out)} out`}
                  </td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {formatDuration(trace.duration_ms)}
                  </td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {trace.error_count === 0 ? (
                      "—"
                    ) : (
                      <span className="inline-flex items-center whitespace-nowrap rounded-full bg-danger-tint px-2.5 py-[3px] text-xs font-medium text-danger-deep">
                        {trace.error_count === 1
                          ? "1 error"
                          : `${trace.error_count} errors`}
                      </span>
                    )}
                  </td>
                  <td className={`${cell} whitespace-nowrap`}>
                    {trace.has_content ? "Full" : "None"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
