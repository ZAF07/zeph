import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TaggingResultPanel } from "@/components/TaggingResultPanel";
import type { TaggingResult } from "@/lib/api-client";
import { taggingCaseSampleResult } from "@/lib/design-fixtures/eval-tagging";

const result: TaggingResult = taggingCaseSampleResult.tagging ?? {
  answered: true,
  kept: [],
  dropped: [],
  expected: [],
};

describe("TaggingResultPanel", () => {
  it("says how the kept Observations differ from those expected", () => {
    render(
      <TaggingResultPanel
        caseKey="conf-yes-to-sister-then-resents"
        result={result}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "conf-yes-to-sister-then-resents" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Failed · 1 not expected")).toBeInTheDocument();
  });

  it("shows each kept Observation's quote, Pattern Type, who, Thread and context", () => {
    render(<TaggingResultPanel caseKey="case" result={result} />);

    expect(
      screen.getByText(
        "“I said yes straight away even though I’d planned to rest”",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("CONF.AVOID.BELONG I2 · for")).toBeInTheDocument();
    expect(screen.getByText("Mei, their sister")).toBeInTheDocument();
    expect(screen.getByText("Helping Mei move")).toBeInTheDocument();
    expect(screen.getByText("None")).toBeInTheDocument();
    expect(
      screen.getByText(/Agreed to help Mei move again/),
    ).toBeInTheDocument();
  });

  it("shows each dropped entry as written and why", () => {
    render(<TaggingResultPanel caseKey="case" result={result} />);

    expect(screen.getByText("Dropped")).toBeInTheDocument();
    expect(screen.getByText("CONF.AVOID.BELONG I5 · for")).toBeInTheDocument();
    expect(
      screen.getByText("quote not word for word in the User's own texts"),
    ).toBeInTheDocument();
  });

  it("says Passed and names an unclear pair when everything matches", () => {
    render(
      <TaggingResultPanel
        caseKey="case"
        result={{
          answered: true,
          expected: [
            {
              pattern_type: "ACH.WORTH.PERF",
              direction: "for",
              unclear: true,
              situational: false,
              matched: true,
            },
          ],
          kept: [
            {
              ...result.kept[0],
              pattern_types: ["CONF.AVOID.BELONG", "ACH.WORTH.PERF"],
              unclear: true,
            },
          ],
          dropped: [],
        }}
      />,
    );

    expect(screen.getByText("Passed")).toBeInTheDocument();
    expect(
      screen.getByText("ACH.WORTH.PERF · for · unclear"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "CONF.AVOID.BELONG or ACH.WORTH.PERF I2 · for · unclear",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Nothing was dropped.")).toBeInTheDocument();
  });

  it("says when nothing was expected and the answer couldn't be read", () => {
    render(
      <TaggingResultPanel
        caseKey="case"
        result={{ answered: false, expected: [], kept: [], dropped: [] }}
      />,
    );

    const panel = screen.getByRole("region", { name: "Result" });
    expect(
      within(panel).getByText("Failed · answer unreadable"),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(/answer couldn’t be read, so nothing was kept/),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText("Nothing to tag, so nothing may be kept."),
    ).toBeInTheDocument();
    expect(within(panel).getByText("Nothing was kept.")).toBeInTheDocument();
  });
});
