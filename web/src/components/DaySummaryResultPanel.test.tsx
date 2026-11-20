import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DaySummaryResultPanel } from "@/components/DaySummaryResultPanel";
import { dayCaseSampleResult } from "@/lib/design-fixtures/eval-day-summary";

const result = dayCaseSampleResult.day_summary ?? {
  summary: "",
  answers: [],
};

describe("DaySummaryResultPanel", () => {
  it("says how many questions missed", () => {
    render(
      <DaySummaryResultPanel caseKey="guilt-and-job-worry" result={result} />,
    );

    expect(
      screen.getByRole("heading", { name: "guilt-and-job-worry" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Failed · 1 of 2 missed")).toBeInTheDocument();
  });

  it("says Passed when every answer matched", () => {
    render(
      <DaySummaryResultPanel
        caseKey="first-10k"
        result={{
          ...result,
          answers: result.answers.map((answer) => ({
            ...answer,
            matched: true,
          })),
        }}
      />,
    );

    expect(screen.getByText("Passed")).toBeInTheDocument();
  });
});
