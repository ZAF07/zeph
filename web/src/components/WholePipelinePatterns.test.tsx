import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WholePipelinePatterns } from "@/components/WholePipelinePatterns";
import type { WholePipelineResult } from "@/lib/api-client";

const result: WholePipelineResult = {
  patterns: [
    {
      pattern_type: "CONF.AVOID.BELONG",
      name: "Softening disagreement to protect belonging",
      is_true: true,
      shared: true,
      state: "shared",
    },
    {
      pattern_type: "APPR.GIVE.NEEDED",
      name: "Saying yes and over-giving to feel needed",
      is_true: false,
      shared: false,
      state: "suspected",
    },
  ],
  missed: [
    {
      pattern_type: "ACH.GOAL.MOVE",
      name: "Moving the goal as soon as they reach it",
      state: "suspected",
      blocked_by: "counter_test",
    },
    {
      pattern_type: "CTRL.SELF.RELY",
      name: "",
      state: null,
      blocked_by: null,
    },
  ],
  true_count: 3,
  conversations: 5,
};

describe("WholePipelinePatterns", () => {
  it("lists each ready or shared Pattern and whether it is a true one", () => {
    render(<WholePipelinePatterns result={result} />);

    expect(
      screen.getByText("5 Conversations · 1 of 3 true Patterns found"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "CONF.AVOID.BELONG · Softening disagreement to protect belonging",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("True")).toBeInTheDocument();
    expect(screen.getByText("Not true")).toBeInTheDocument();
    expect(screen.getAllByText("Shared")).toHaveLength(2);
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it("lists each true Pattern missed and what stopped it", () => {
    render(<WholePipelinePatterns result={result} />);

    expect(screen.getAllByText("Missed")).toHaveLength(2);
    expect(screen.getByText("No answered counter-test")).toBeInTheDocument();
    expect(screen.getByText("CTRL.SELF.RELY")).toBeInTheDocument();
    expect(screen.getByText("Never noticed")).toBeInTheDocument();
    expect(screen.getByText("Nothing yet")).toBeInTheDocument();
  });

  it("says so when nothing became ready and nothing is true", () => {
    render(
      <WholePipelinePatterns
        result={{ patterns: [], missed: [], true_count: 0, conversations: 4 }}
      />,
    );

    expect(
      screen.getByText("4 Conversations · 0 of 0 true Patterns found"),
    ).toBeInTheDocument();
    expect(screen.getByText("No Pattern became ready.")).toBeInTheDocument();
    expect(
      screen.getByText("None is true of this made-up User."),
    ).toBeInTheDocument();
  });

  it("says none was missed when every true Pattern was found", () => {
    render(
      <WholePipelinePatterns
        result={{ ...result, missed: [], true_count: 1 }}
      />,
    );

    expect(screen.getByText("None missed.")).toBeInTheDocument();
  });
});
