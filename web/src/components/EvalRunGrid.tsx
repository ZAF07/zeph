"use client";

import Link from "next/link";
import { useState } from "react";

import { CaseResultCard } from "@/components/CaseResultCard";
import { EvalPill } from "@/components/EvalPill";
import { tableHeadCell } from "@/components/table-styles";
import { TableCards, type TableColumn } from "@/components/TableCards";
import type { EvalRunDetails, VariantTotals } from "@/lib/api-client";
import { describeCost, describeTotals } from "@/lib/evals";
import { formatDuration, formatTokens } from "@/lib/model-calls";
import {
  cellKey,
  describeTriesUsage,
  resultsByCell,
  triesPill,
} from "@/lib/eval-run-grid";

/** One phone card of the grid: a case's row, or the Variants' totals. */
type GridCardRow = { kind: "case"; caseKey: string } | { kind: "totals" };

/**
 * Gives a phone card its key. The totals card's key can't be a case key.
 *
 * @param row - The card's row.
 * @returns The key.
 */
function cardRowKey(row: GridCardRow): string {
  return row.kind === "totals" ? "\u0000totals" : row.caseKey;
}

/**
 * The link from a case's key to its history in recent runs.
 *
 * @param caseKey - The case.
 * @returns The link.
 */
function caseLink(caseKey: string) {
  return (
    <Link
      href={`/admin/evals/history/${encodeURIComponent(caseKey)}`}
      title="This case in recent runs"
      className="underline"
    >
      {caseKey}
    </Link>
  );
}

/**
 * A run's Case Results side by side: a row per case and a column per
 * Variant, each cell showing how its tries went with their tokens and time,
 * then each Variant's totals. Picking a cell opens its tries below the grid,
 * each with the Judge's reasons and a link to its full trace.
 *
 * @param props - `run` is the run with its results and Variant totals.
 * @returns The grid, then the picked cell's tries.
 */
export function EvalRunGrid({ run }: { run: EvalRunDetails }) {
  const [picked, setPicked] = useState<{
    caseKey: string;
    letter: string;
  } | null>(null);
  const cells = resultsByCell(run.results);
  const pickedTries = picked
    ? (cells.get(cellKey(picked.caseKey, picked.letter)) ?? [])
    : [];

  /**
   * One cell of the grid: how a case's tries went on a Variant, as a button
   * that opens them, or a dash before any try has finished.
   *
   * @param caseKey - The case.
   * @param letter - The Variant's letter.
   * @returns The cell's content.
   */
  function triesCell(caseKey: string, letter: string) {
    const tries = cells.get(cellKey(caseKey, letter)) ?? [];
    const isPicked = picked?.caseKey === caseKey && picked.letter === letter;
    if (tries.length === 0) {
      return <span className="px-1.5 text-mute">—</span>;
    }
    return (
      <button
        type="button"
        aria-pressed={isPicked}
        aria-label={`${caseKey} on Variant ${letter}`}
        onClick={() => setPicked(isPicked ? null : { caseKey, letter })}
        className={`flex w-full cursor-pointer flex-col items-start gap-1 rounded-input border px-1.5 py-1.5 text-left font-[inherit] text-[13px] text-text ${
          isPicked
            ? "border-line-strong bg-zeph"
            : "border-transparent bg-transparent hover:bg-bg-deep"
        }`}
      >
        <EvalPill {...triesPill(tries, run.repeats)} />
        <span className="whitespace-nowrap text-soft">
          {describeTriesUsage(tries)}
        </span>
      </button>
    );
  }

  /**
   * A Variant's totals: passes, tokens, time and cost.
   *
   * @param totals - The Variant's totals.
   * @returns The lines.
   */
  function totalsLines(totals: VariantTotals) {
    return (
      <>
        <p className="m-0">{describeTotals(totals)}</p>
        <p className="m-0 whitespace-nowrap text-soft">
          {formatTokens(totals.tokens_in, totals.tokens_out)}
        </p>
        <p className="m-0 text-soft">
          {formatDuration(totals.duration_ms)} · {describeCost(totals)}
        </p>
      </>
    );
  }

  const cardRows: GridCardRow[] = [
    ...run.case_keys.map((caseKey) => ({ kind: "case" as const, caseKey })),
    { kind: "totals" },
  ];
  const cardColumns: TableColumn<GridCardRow>[] = [
    {
      heading: "Case",
      cell: (row) => (row.kind === "totals" ? "Totals" : caseLink(row.caseKey)),
    },
    ...run.variants.map((variant) => ({
      heading: `Variant ${variant.letter}`,
      cell: (row: GridCardRow) => {
        if (row.kind === "case") {
          return triesCell(row.caseKey, variant.letter);
        }
        const totals = run.variant_totals.find(
          (other) => other.letter === variant.letter,
        );
        return totals ? totalsLines(totals) : null;
      },
    })),
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-x-auto rounded-card border border-line bg-panel max-[899px]:hidden">
        <table className="w-full border-collapse text-left text-[13px] text-text">
          <thead>
            <tr>
              <th scope="col" className={tableHeadCell}>
                Case
              </th>
              {run.variants.map((variant) => (
                <th key={variant.letter} scope="col" className={tableHeadCell}>
                  Variant {variant.letter}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {run.case_keys.map((caseKey) => (
              <tr key={caseKey} className="border-t border-line">
                <th scope="row" className="px-[18px] py-2.5 font-normal">
                  {caseLink(caseKey)}
                </th>
                {run.variants.map((variant) => (
                  <td key={variant.letter} className="px-2 py-1.5">
                    {triesCell(caseKey, variant.letter)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th
                scope="row"
                className="border-t border-line px-[18px] py-2.5 align-top font-normal"
              >
                Totals
              </th>
              {run.variant_totals.map((totals) => (
                <td
                  key={totals.letter}
                  aria-label={`Variant ${totals.letter} totals`}
                  className="border-t border-line px-[18px] py-2.5 align-top"
                >
                  {totalsLines(totals)}
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
      <TableCards columns={cardColumns} rows={cardRows} rowKey={cardRowKey} />
      {picked ? (
        <section
          aria-label={`${picked.caseKey} on Variant ${picked.letter}`}
          className="flex flex-col gap-2.5"
        >
          <h2 className="m-0 text-[17px] font-normal text-cream">
            {picked.caseKey} on Variant {picked.letter}
            {run.repeats > 1
              ? ` · ${pickedTries.length} of ${run.repeats} tries done`
              : ""}
          </h2>
          <ol className="m-0 flex list-none flex-col gap-2.5 p-0">
            {pickedTries.map((result) => (
              <CaseResultCard
                key={result.id}
                runId={run.id}
                result={result}
                tryLabel={
                  run.repeats > 1
                    ? `Try ${result.try_number} of ${run.repeats}`
                    : undefined
                }
              />
            ))}
          </ol>
        </section>
      ) : (
        <p className="m-0 text-[13px] text-soft">
          Pick a cell to see the Judge’s reasons and open each try’s full trace.
        </p>
      )}
    </div>
  );
}
