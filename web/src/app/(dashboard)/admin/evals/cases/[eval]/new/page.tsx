import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { cardLink } from "@/components/card-styles";
import { DaySummaryResultPanel } from "@/components/DaySummaryResultPanel";
import { DesignNote } from "@/components/DesignNote";
import { EvalCaseEditor } from "@/components/EvalCaseEditor";
import { env } from "@/env";
import {
  dayCaseDraft,
  dayCaseSampleResult,
} from "@/lib/design-fixtures/eval-day-summary";
import { evalDetails, toEvalName } from "@/lib/evals";

/**
 * The admin page for adding a case to an Eval. In design-fixture mode the
 * Day Summary case form opens filled in, with the drawn sample result and
 * notes under it.
 *
 * @param props - `params` holds the Eval's name from the address.
 * @returns The page.
 */
export default async function AdminNewEvalCasePage({
  params,
}: {
  params: Promise<{ eval: string }>;
}) {
  const evalName = toEvalName((await params).eval);
  if (evalName === null) {
    notFound();
  }
  const isDesignSample = env.designFixtures && evalName === "day_summary";
  return (
    <>
      <Link
        href={`/admin/evals/cases/${evalName}`}
        className={`${cardLink} w-fit`}
      >
        ← {evalDetails[evalName].label} cases
      </Link>
      <AdminPageHeader
        title={`New ${evalDetails[evalName].label} case`}
        lead={evalDetails[evalName].checks}
        aside={
          isDesignSample ? (
            <span className="rounded-pill border border-line-strong px-3 py-1 text-[12px] text-soft">
              Sample data
            </span>
          ) : undefined
        }
      />
      <EvalCaseEditor
        evalName={evalName}
        draft={isDesignSample ? dayCaseDraft : undefined}
      />
      {isDesignSample && dayCaseSampleResult.day_summary ? (
        <>
          <DesignNote title="How a result reads, on a run" />
          <DaySummaryResultPanel
            caseKey={dayCaseSampleResult.case_key}
            result={dayCaseSampleResult.day_summary}
          />
          <DesignNote title="About this page" />
          <p className="m-0 max-w-[760px] text-[14px] text-soft">
            Every Eval case form has this shape: Key, then one panel per part of
            the case, each with a hint, repeated entries in inset groups with
            their own Remove, and an Add button under the last one. Editing a
            saved case drops the Key panel and the button reads “Save case”.
          </p>
        </>
      ) : null}
    </>
  );
}
