import { act, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EvalRunView, runCheckMilliseconds } from "@/components/EvalRunView";
import type { ApiClient, CaseResult, EvalRunDetails } from "@/lib/api-client";
import { finishedRun, passedResult } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getEvalRun: vi.fn<ApiClient["getEvalRun"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const failedResult: CaseResult = {
  ...passedResult,
  id: "result-2",
  case_key: "reminded-of-sister",
  eval: "understanding",
  outcome: "fail",
  checks: [
    {
      name: "need",
      passed: true,
      detail: "picked Be heard",
      group: "my sister's wedding is next week",
    },
    {
      name: "no_fixing",
      passed: false,
      detail: "Suggests a lawyer.",
      group: "my sister's wedding is next week",
    },
  ],
  notes: ["Person: my sister's wedding is next week", "Zeph: Have you tried…"],
};
const erroredResult: CaseResult = {
  ...passedResult,
  id: "result-3",
  case_key: "traffic",
  outcome: "error",
  checks: [],
  error: "The model didn't answer",
};

const running: EvalRunDetails = {
  ...finishedRun,
  state: "running",
  finished_at: null,
  case_count: 3,
  passed: 1,
  tokens_in: 900,
  tokens_out: 40,
  results: [passedResult],
};
const finished: EvalRunDetails = {
  ...finishedRun,
  case_count: 3,
  passed: 1,
  failed: 1,
  errored: 1,
  tokens_in: 2700,
  tokens_out: 120,
  results: [passedResult, failedResult, erroredResult],
};

async function waitForNextCheck() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(runCheckMilliseconds);
  });
}

describe("EvalRunView", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("fills in Case Results while running and stops checking once finished", async () => {
    apiClient.getEvalRun
      .mockResolvedValueOnce(running)
      .mockResolvedValue(finished);
    renderWithQueries(<EvalRunView runId="run-1" />);

    expect(await screen.findByText("1 of 3 cases done")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    await waitForNextCheck();

    expect(await screen.findByText("3 of 3 cases done")).toBeInTheDocument();
    expect(screen.getByText("Finished")).toBeInTheDocument();
    expect(
      screen.getByText("1 passed · 1 failed · 1 error"),
    ).toBeInTheDocument();
    const calls = apiClient.getEvalRun.mock.calls.length;
    await waitForNextCheck();
    await waitForNextCheck();
    expect(apiClient.getEvalRun).toHaveBeenCalledTimes(calls);
    expect(apiClient.getEvalRun).toHaveBeenCalledWith("run-1");
  });

  it("shows the Judge's reason per rule, grouped by Message, and errors apart", async () => {
    apiClient.getEvalRun.mockResolvedValue(finished);
    renderWithQueries(<EvalRunView runId="run-1" />);

    const failedCard = await screen.findByRole("listitem", {
      name: "reminded-of-sister",
    });
    const erroredCard = screen.getByRole("listitem", { name: "traffic" });
    expect(
      screen.getByText("“my sister's wedding is next week”"),
    ).toBeVisible();
    expect(screen.getByText(/Suggests a lawyer\./)).toBeInTheDocument();
    expect(screen.getByText("2 checks, 1 failed")).toBeInTheDocument();
    expect(within(failedCard).getByText("Fail")).toBeInTheDocument();
    expect(
      within(erroredCard).getByText(
        "Couldn’t be checked: The model didn't answer",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/don’t count as fails/)).toBeInTheDocument();
  });

  it("says a Queued run is waiting for the runner", async () => {
    apiClient.getEvalRun.mockResolvedValue({
      ...finishedRun,
      state: "queued",
      case_count: null,
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    expect(
      await screen.findByText(/Waiting for the runner/),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Case Results appear here as each case finishes."),
    ).toBeInTheDocument();
  });
});
