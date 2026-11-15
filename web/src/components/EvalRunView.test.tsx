import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EvalRunView, runCheckMilliseconds } from "@/components/EvalRunView";
import type { ApiClient, CaseResult, EvalRunDetails } from "@/lib/api-client";
import { finishedRun, passedResult } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getEvalRun: vi.fn<ApiClient["getEvalRun"]>(),
  cancelEvalRun: vi.fn<ApiClient["cancelEvalRun"]>(),
  rerunFailedCases: vi.fn<ApiClient["rerunFailedCases"]>(),
  deleteEvalRun: vi.fn<ApiClient["deleteEvalRun"]>(),
  getEvalRunSnapshot: vi.fn<ApiClient["getEvalRunSnapshot"]>(),
};
const router = { push: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
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
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    expect(
      await screen.findByText(/Waiting for the runner/),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Case Results appear here as each case finishes."),
    ).toBeInTheDocument();
  });

  it("shows the running cost and cancels a running run after its case", async () => {
    const withCost = { ...running, cost_sgd: 0.0123 };
    apiClient.getEvalRun.mockResolvedValue(withCost);
    apiClient.cancelEvalRun.mockResolvedValue({
      ...withCost,
      cancel_requested: true,
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    expect(await screen.findByText("S$0.0123")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Re-run failed/ }),
    ).not.toBeInTheDocument();
    apiClient.getEvalRun.mockResolvedValue({
      ...withCost,
      cancel_requested: true,
    });
    await userEvent.click(screen.getByRole("button", { name: "Cancel run" }));

    expect(apiClient.cancelEvalRun).toHaveBeenCalledWith("run-1");
    expect(
      await screen.findByRole("button", { name: "Cancelling…" }),
    ).toBeDisabled();
    expect(
      screen.getByText(/stops after the case it is on/),
    ).toBeInTheDocument();
  });

  it("marks models with no price and says why a run stopped over its limit", async () => {
    apiClient.getEvalRun.mockResolvedValue({
      ...finished,
      state: "stopped_over_limit",
      cost_sgd: 0,
      unpriced_models: ["deepseek-x"],
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    expect(
      await screen.findByText("deepseek-x (no price set)"),
    ).toBeInTheDocument();
    expect(screen.getByText("Stopped over limit")).toBeInTheDocument();
    expect(
      screen.getByText(/went over its token limit of 1,000,000/),
    ).toBeInTheDocument();
  });

  it("re-runs the failed cases of an ended run and opens the new run", async () => {
    apiClient.getEvalRun.mockResolvedValue(finished);
    apiClient.rerunFailedCases.mockResolvedValue({
      ...finishedRun,
      id: "run-2",
      state: "queued",
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Re-run failed · 2 cases" }),
    );

    expect(apiClient.rerunFailedCases).toHaveBeenCalledWith("run-1");
    expect(router.push).toHaveBeenCalledWith("/admin/evals/runs/run-2");
  });

  it("deletes a run only after the confirm step", async () => {
    apiClient.getEvalRun.mockResolvedValue(finished);
    apiClient.deleteEvalRun.mockResolvedValue();
    renderWithQueries(<EvalRunView runId="run-1" />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Delete run" }),
    );
    expect(apiClient.deleteEvalRun).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Delete for good" }),
    );

    expect(apiClient.deleteEvalRun).toHaveBeenCalledWith("run-1");
    expect(router.push).toHaveBeenCalledWith("/admin/evals");
  });

  it("links each Case Result to its full trace and its case history", async () => {
    apiClient.getEvalRun.mockResolvedValue(finished);
    renderWithQueries(<EvalRunView runId="run-1" />);

    const card = await screen.findByRole("listitem", { name: "plan" });

    expect(
      within(card).getByRole("link", { name: "Full trace" }),
    ).toHaveAttribute("href", "/admin/evals/runs/run-1/results/result-1");
    expect(within(card).getByRole("link", { name: "plan" })).toHaveAttribute(
      "href",
      "/admin/evals/history/plan",
    );
  });

  it("shows what the run used once opened", async () => {
    apiClient.getEvalRun.mockResolvedValue(finished);
    apiClient.getEvalRunSnapshot.mockResolvedValue({
      settings: { persona: "Warm and plain." },
      judge: { model: "deepseek-flash" },
      cases: [
        {
          key: "plan",
          eval: "safeguard",
          content: { kind: "clear_crisis" },
          archived: false,
        },
      ],
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    await userEvent.click(await screen.findByText("What this run used"));

    expect(await screen.findByText("Warm and plain.")).toBeInTheDocument();
    expect(screen.getByText("Cases (1)")).toBeInTheDocument();
    expect(apiClient.getEvalRunSnapshot).toHaveBeenCalledWith("run-1");
  });
});
