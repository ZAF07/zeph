"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { primaryButton, rowActionButton } from "@/components/button-styles";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DataTable } from "@/components/DataTable";
import { EvalCaseDuplicateDialog } from "@/components/EvalCaseDuplicateDialog";
import { FilterPillLinks } from "@/components/FilterPillLinks";
import { LoadFailed } from "@/components/LoadFailed";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import type { EvalCase, EvalName } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import { evalDetails, evalOrder } from "@/lib/evals";
import { queryKeys, refreshEvalCases } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The address of an Eval Case's editor.
 *
 * @param evalCase - The case.
 * @returns The address.
 */
function editHrefOf(evalCase: EvalCase): string {
  return `/admin/evals/cases/${evalCase.eval}/edit/${evalCase.key}`;
}

/**
 * The address of one Eval's cases.
 *
 * @param evalName - The Eval.
 * @returns The address.
 */
function casesHrefOf(evalName: EvalName): string {
  return `/admin/evals/cases/${evalName}`;
}

const evalLinks = evalOrder.map((name) => ({
  href: casesHrefOf(name),
  label: evalDetails[name].label,
}));

/**
 * One Eval's cases, archived ones too, with links to the other Evals and
 * a button to add a case. Each case can be edited, duplicated (asking for
 * the copy's key, then opening the copy) or archived (after confirming).
 * Built from the admin table template.
 *
 * @param props - `evalName` is the Eval whose cases are shown.
 * @returns The filters and table, or a loading, empty or error state in
 *   place of the table.
 */
export function EvalCasesList({ evalName }: { evalName: EvalName }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [duplicating, setDuplicating] = useState<EvalCase | null>(null);
  const [archiving, setArchiving] = useState<EvalCase | null>(null);
  const casesQuery = useQuery({
    queryKey: queryKeys.evalCases(evalName),
    queryFn: () => apiClient.listEvalCases(evalName),
  });
  const cases = casesQuery.data;

  const archiveMutation = useMutation({
    mutationFn: (key: string) => apiClient.archiveEvalCase(key),
    onSuccess: () => refreshEvalCases(queryClient),
    onSettled: () => setArchiving(null),
  });

  const columns: TableColumn<EvalCase>[] = [
    {
      heading: "Case",
      isMain: true,
      cell: (evalCase) => (
        <Link
          href={editHrefOf(evalCase)}
          className="break-all text-text underline"
        >
          {evalCase.key}
        </Link>
      ),
    },
    {
      heading: "Status",
      cell: (evalCase) =>
        evalCase.archived || evalCase.edited ? (
          <span className="inline-flex flex-wrap gap-1.5">
            {evalCase.archived ? (
              <StatusPill filled={false}>Archived</StatusPill>
            ) : null}
            {evalCase.edited ? (
              <StatusPill filled={false}>Edited</StatusPill>
            ) : null}
          </span>
        ) : (
          "—"
        ),
    },
    {
      heading: "Changed",
      cell: (evalCase) =>
        evalCase.updated_by_name
          ? `Changed ${formatSavedAt(evalCase.updated_at)} by ${evalCase.updated_by_name}`
          : "From the seed files",
    },
    {
      heading: "Actions",
      cell: (evalCase) => (
        <span className="inline-flex gap-4">
          <Link href={editHrefOf(evalCase)} className={rowActionButton}>
            {evalCase.archived ? "View" : "Edit"}
          </Link>
          <button
            type="button"
            className={rowActionButton}
            onClick={() => setDuplicating(evalCase)}
          >
            Duplicate
          </button>
          {evalCase.archived ? null : (
            <button
              type="button"
              className={rowActionButton}
              onClick={() => setArchiving(evalCase)}
            >
              Archive
            </button>
          )}
        </span>
      ),
    },
  ];

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <FilterPillLinks
          label="Evals"
          links={evalLinks}
          currentHref={casesHrefOf(evalName)}
        />
        <Link href={`${casesHrefOf(evalName)}/new`} className={primaryButton}>
          Add case
        </Link>
      </div>

      {archiveMutation.isError ? (
        <SaveFailedNote>Couldn’t archive the case. Try again.</SaveFailedNote>
      ) : null}

      {casesQuery.isPending ? <TableLoading label="Loading cases" /> : null}

      {cases === undefined && casesQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the cases"
          body="Nothing was changed."
          onRetry={() => void casesQuery.refetch()}
        />
      ) : null}

      {cases !== undefined && cases.length === 0 ? (
        <TableEmpty
          title={`No ${evalDetails[evalName].label} cases yet`}
          body="Add a case to check a situation you saw go wrong."
        />
      ) : null}

      {cases !== undefined && cases.length > 0 ? (
        <DataTable
          columns={columns}
          rows={cases}
          rowKey={(evalCase) => evalCase.key}
          minWidthClass="min-w-[720px]"
        />
      ) : null}

      {duplicating ? (
        <EvalCaseDuplicateDialog
          evalCase={duplicating}
          onClose={() => setDuplicating(null)}
        />
      ) : null}

      {archiving ? (
        <ConfirmDialog
          open
          title={`Archive ${archiving.key}?`}
          body="New runs leave it out; past runs still show it. Archived cases can’t be edited."
          cancelLabel="Keep it"
          confirmLabel="Archive"
          onConfirm={() => archiveMutation.mutate(archiving.key)}
          onCancel={() => setArchiving(null)}
        />
      ) : null}
    </>
  );
}
