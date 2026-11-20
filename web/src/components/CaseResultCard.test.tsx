import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CaseResultCard } from "@/components/CaseResultCard";
import { dayCaseSampleResult } from "@/lib/design-fixtures/eval-day-summary";
import { passedResult } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

describe("CaseResultCard", () => {
  it("shows a Day Summary case's Summary and each question, matched or missed", () => {
    renderWithQueries(
      <ul>
        <CaseResultCard runId="run-1" result={dayCaseSampleResult} />
      </ul>,
    );

    const card = screen.getByRole("listitem", { name: "guilt-and-job-worry" });
    expect(within(card).getByText("Day Summary written")).toBeInTheDocument();
    expect(
      within(card).getByText(/Later traced the short temper/),
    ).toBeInTheDocument();
    expect(within(card).getByText("Match")).toBeInTheDocument();
    expect(within(card).getByText("Miss")).toBeInTheDocument();
    expect(
      within(card).getByText("The Summary does not say what Zeph offered."),
    ).toBeInTheDocument();
    expect(
      within(card).getByText(/leaves out what Zeph offered and how the User/),
    ).toBeInTheDocument();
    expect(within(card).queryByText(/checks?,/)).not.toBeInTheDocument();
  });

  it("shows another Eval's checks as before", () => {
    renderWithQueries(
      <ul>
        <CaseResultCard runId="run-1" result={passedResult} />
      </ul>,
    );

    expect(screen.queryByText("Day Summary written")).not.toBeInTheDocument();
  });
});
