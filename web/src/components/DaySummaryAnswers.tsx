import { EvalPill } from "@/components/EvalPill";
import type { DaySummaryResult } from "@/lib/api-client";

/**
 * What a Day Summary case wrote and how the Judge answered from it: the
 * Summary, then each question with the answer expected, the Judge's answer
 * from the Summary alone, Match or Miss, and the Judge's reason.
 *
 * @param props - `result` is the case's Day Summary and answers.
 * @returns The Summary and the questions.
 */
export function DaySummaryAnswers({ result }: { result: DaySummaryResult }) {
  return (
    <>
      <div>
        <div className="pb-1.5 text-[12px] text-soft">Day Summary written</div>
        <pre className="m-0 box-border rounded-input border border-line bg-bg-deep px-3.5 py-3 font-mono text-[13px] leading-[1.6] whitespace-pre-wrap text-text">
          {result.summary || "No Day Summary was written."}
        </pre>
      </div>
      <div>
        {result.answers.map((answer, index) => (
          <div
            key={index}
            className={`flex flex-col gap-2 py-3.5 ${index > 0 ? "border-t border-line" : ""}`}
          >
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
              <span className="min-w-0 flex-[1_1_320px] text-[15px] font-normal text-text">
                {answer.question}
              </span>
              {answer.matched ? (
                <EvalPill label="Match" pill="bg-cream text-ink" />
              ) : (
                <EvalPill
                  label="Miss"
                  pill="border border-danger text-danger"
                />
              )}
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-[14px]">
              <div className="min-w-0 flex-[1_1_280px]">
                <div className="text-[12px] text-soft">Expected</div>
                <div className="text-text">{answer.expected}</div>
              </div>
              <div className="min-w-0 flex-[1_1_280px]">
                <div className="text-[12px] text-soft">
                  Judge’s answer, from the Summary alone
                </div>
                <div className="text-text">{answer.answer || "Not asked."}</div>
              </div>
            </div>
            <div className="text-[13px] text-soft">
              <span className="text-text">Judge’s reason.</span> {answer.reason}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
