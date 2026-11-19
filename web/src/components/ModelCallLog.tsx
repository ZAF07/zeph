"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataTable } from "@/components/DataTable";
import { FilterToggle } from "@/components/FilterToggle";
import { LoadFailed } from "@/components/LoadFailed";
import { SelectFilter } from "@/components/SelectFilter";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import { TableNoMatches } from "@/components/TableNoMatches";
import type {
  ModelCallTrace,
  ModelCallTraceFilter,
  ModelStep,
} from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import {
  describeSteps,
  formatDuration,
  formatTokens,
  modelSteps,
  traceKindLabel,
} from "@/lib/model-calls";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const periods = [
  { value: "1", label: "Last 24 hours" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
];

const stepOptions = [
  { value: "", label: "All steps" },
  ...modelSteps.map((step) => ({ value: step.id, label: step.label })),
];

const columns: TableColumn<ModelCallTrace>[] = [
  {
    heading: "Time",
    isMain: true,
    cell: (trace) => (
      <Link
        href={`/admin/model-calls/${trace.trace_id}`}
        className="whitespace-nowrap text-text underline"
      >
        {formatSavedAt(trace.started_at)}
      </Link>
    ),
  },
  {
    heading: "User",
    isMain: true,
    cell: (trace) => trace.user_name ?? trace.user_email ?? "Unknown User",
  },
  { heading: "For", cell: (trace) => traceKindLabel(trace.kind) },
  { heading: "Steps", cell: (trace) => describeSteps(trace.steps) },
  {
    heading: "Tokens",
    cell: (trace) => formatTokens(trace.tokens_in, trace.tokens_out),
  },
  {
    heading: "Time taken",
    cell: (trace) => formatDuration(trace.duration_ms),
  },
  {
    heading: "Errors",
    cell: (trace) =>
      trace.error_count === 0 ? (
        "—"
      ) : (
        <StatusPill filled={false} danger>
          {trace.error_count === 1 ? "1 error" : `${trace.error_count} errors`}
        </StatusPill>
      ),
  },
  {
    heading: "Content",
    cell: (trace) => (trace.has_content ? "Full" : "None"),
  },
];

/**
 * Reads a step filter's value back into a step.
 *
 * @param value - The chosen option's value; empty for all steps.
 * @returns The step, or an empty string for all steps.
 */
function toStep(value: string): ModelStep | "" {
  return modelSteps.find((step) => step.id === value)?.id ?? "";
}

/**
 * The admin Model Call Log: one trace per Message, Check-in or Conversation
 * end, newest first, filtered by User, step, period and errors. Each trace
 * opens on its own page. Content is only ever there for Admins' own chats
 * and Evals. Built from the admin table template.
 *
 * @returns The filters and table, or a loading, no-match, empty or error
 *   state in place of the table.
 */
export function ModelCallLog() {
  const apiClient = useApiClient();
  const [userId, setUserId] = useState("");
  const [step, setStep] = useState<ModelStep | "">("");
  const [period, setPeriod] = useState("7");
  const [errorsOnly, setErrorsOnly] = useState(false);

  const filter: ModelCallTraceFilter = {
    days: Number(period),
    ...(userId ? { userId } : {}),
    ...(step ? { step } : {}),
    ...(errorsOnly ? { errorsOnly } : {}),
  };
  const isNarrowed = userId !== "" || step !== "" || errorsOnly;
  const tracesQuery = useQuery({
    queryKey: queryKeys.modelCallTraces(filter),
    queryFn: () => apiClient.listModelCallTraces(filter),
  });
  const usersQuery = useQuery({
    queryKey: queryKeys.adminUsers,
    queryFn: () => apiClient.listAdminUsers(),
  });
  const traces = tracesQuery.data;
  const userOptions = [
    { value: "", label: "All Users" },
    ...(usersQuery.data ?? []).map((user) => ({
      value: user.id,
      label: user.name ?? user.email ?? "Unknown User",
    })),
  ];

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <SelectFilter
          label="User"
          options={userOptions}
          value={userId}
          onChange={setUserId}
        />
        <SelectFilter
          label="Step"
          options={stepOptions}
          value={step}
          onChange={(value) => setStep(toStep(value))}
        />
        <SelectFilter
          label="Period"
          options={periods}
          value={period}
          onChange={setPeriod}
        />
        <FilterToggle
          label="Errors only"
          on={errorsOnly}
          onChange={setErrorsOnly}
        />
      </div>

      {tracesQuery.isPending ? <TableLoading label="Loading log" /> : null}

      {traces === undefined && tracesQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Model Call Log"
          body="The Companion is still replying as normal."
          onRetry={() => void tracesQuery.refetch()}
        />
      ) : null}

      {traces !== undefined && traces.length === 0 && isNarrowed ? (
        <TableNoMatches />
      ) : null}

      {traces !== undefined && traces.length === 0 && !isNarrowed ? (
        <TableEmpty
          title="No model calls yet"
          body="Traces appear as the Companion answers Messages, sends Check-ins and wraps up Conversations. Nothing matches these filters yet."
        />
      ) : null}

      {traces !== undefined && traces.length > 0 ? (
        <DataTable
          columns={columns}
          rows={traces}
          rowKey={(trace) => trace.trace_id}
          minWidthClass="min-w-[920px]"
        />
      ) : null}
    </>
  );
}
