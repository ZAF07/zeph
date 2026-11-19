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
  listSettingOverrideChoices: vi.fn<ApiClient["listSettingOverrideChoices"]>(),
  listLiveChanges: vi.fn<ApiClient["listLiveChanges"]>(),
  makeVariantLive: vi.fn<ApiClient["makeVariantLive"]>(),
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
  case_keys: ["plan", "reminded-of-sister", "traffic"],
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

function grid() {
  return within(screen.getByRole("table"));
}

async function findGrid() {
  return within(await screen.findByRole("table"));
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

    await userEvent.click(
      await (
        await findGrid()
      ).findByRole("button", {
        name: "reminded-of-sister on Variant A",
      }),
    );
    const failedCard = screen.getByRole("listitem", {
      name: "reminded-of-sister",
    });
    expect(within(failedCard).getByText("Fail")).toBeInTheDocument();
    expect(
      screen.getByText("“my sister's wedding is next week”"),
    ).toBeVisible();
    expect(screen.getByText(/Suggests a lawyer\./)).toBeInTheDocument();
    expect(screen.getByText("2 checks, 1 failed")).toBeInTheDocument();
    await userEvent.click(
      grid().getByRole("button", { name: "traffic on Variant A" }),
    );
    const erroredCard = screen.getByRole("listitem", { name: "traffic" });
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

    await userEvent.click(
      await (
        await findGrid()
      ).findByRole("button", { name: "plan on Variant A" }),
    );
    const card = screen.getByRole("listitem", { name: "plan" });

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
      needs: [],
      moves: [],
    });
    renderWithQueries(<EvalRunView runId="run-1" />);

    await userEvent.click(await screen.findByText("What this run used"));

    expect(await screen.findByText("Warm and plain.")).toBeInTheDocument();
    expect(screen.getByText("Cases (1)")).toBeInTheDocument();
    expect(apiClient.getEvalRunSnapshot).toHaveBeenCalledWith("run-1");
  });

  describe("comparing Variants", () => {
    const tryOf = (
      id: string,
      variant: string,
      tryNumber: number,
      outcome: CaseResult["outcome"],
    ): CaseResult => ({
      ...passedResult,
      id,
      variant,
      try_number: tryNumber,
      outcome,
    });
    const comparison: EvalRunDetails = {
      ...finishedRun,
      case_keys: ["plan"],
      repeats: 2,
      case_count: 4,
      variants: [
        { letter: "A", setting_overrides: {}, made_live: null },
        {
          letter: "B",
          setting_overrides: { understanding_thinking: false },
          made_live: null,
        },
      ],
      results: [
        tryOf("a-1", "A", 1, "pass"),
        tryOf("b-1", "B", 1, "fail"),
        tryOf("a-2", "A", 2, "pass"),
        tryOf("b-2", "B", 2, "pass"),
      ],
      variant_totals: [
        {
          letter: "A",
          passed: 2,
          failed: 0,
          errored: 0,
          tokens_in: 1800,
          tokens_out: 80,
          duration_ms: 4800,
          cost_sgd: 0.0021,
          unpriced_models: [],
        },
        {
          letter: "B",
          passed: 1,
          failed: 1,
          errored: 0,
          tokens_in: 1000,
          tokens_out: 60,
          duration_ms: 2000,
          cost_sgd: 0.0011,
          unpriced_models: [],
        },
      ],
    };

    beforeEach(() => {
      apiClient.listSettingOverrideChoices.mockResolvedValue({
        settings: [
          {
            key: "understanding_thinking",
            label: "Understanding thinking",
            kind: "on_off",
            minimum: 0,
            maximum: 0,
            max_length: 20000,
            hint: null,
            value: true,
          },
        ],
        needs: [],
        moves: [],
        models: ["deepseek-flash"],
      });
      apiClient.getEvalRunSnapshot.mockResolvedValue({
        settings: { understanding_thinking: true },
        judge: {},
        cases: [],
        needs: [],
        moves: [
          {
            key: "move:m-1",
            name: "Research",
            value: {
              name: "Research",
              when_it_fits: "They need options found.",
              how_to_do_it: "Search and compare.",
            },
          },
        ],
      });
    });

    it("shows a column per Variant with each cell's tries and totals", async () => {
      apiClient.getEvalRun.mockResolvedValue(comparison);
      renderWithQueries(<EvalRunView runId="run-1" />);

      const cellB = await (
        await findGrid()
      ).findByRole("button", {
        name: "plan on Variant B",
      });
      expect(within(cellB).getByText("1 of 2 passed")).toBeInTheDocument();
      expect(
        within(
          grid().getByRole("button", { name: "plan on Variant A" }),
        ).getByText("2 of 2 passed"),
      ).toBeInTheDocument();
      const totalsB = screen.getByRole("cell", { name: "Variant B totals" });
      expect(
        within(totalsB).getByText("1 passed · 1 failed"),
      ).toBeInTheDocument();
      expect(within(totalsB).getByText("2.0 s · S$0.0011")).toBeInTheDocument();

      await userEvent.click(cellB);

      const tries = screen.getAllByRole("listitem", { name: "plan" });
      expect(tries).toHaveLength(2);
      expect(within(tries[0]).getByText("· Try 1 of 2")).toBeInTheDocument();
      expect(within(tries[0]).getByText("Fail")).toBeInTheDocument();
      expect(
        within(tries[1]).getByRole("link", { name: "Full trace" }),
      ).toHaveAttribute("href", "/admin/evals/runs/run-1/results/b-2");
    });

    it("shows each override as a difference from live when the run started", async () => {
      apiClient.getEvalRun.mockResolvedValue(comparison);
      renderWithQueries(<EvalRunView runId="run-1" />);

      const variantB = await screen.findByRole("region", { name: "Variant B" });
      expect(
        await within(variantB).findByText("Understanding thinking"),
      ).toBeInTheDocument();
      expect(
        within(variantB).getByText("Live when it started:").parentElement,
      ).toHaveTextContent("Live when it started: On");
      expect(
        within(variantB).getByText("Variant B:").parentElement,
      ).toHaveTextContent("Variant B: Off");
      const variantA = screen.getByRole("region", { name: "Variant A" });
      expect(within(variantA).getByText(/live settings/)).toBeInTheDocument();
      expect(
        within(variantA).queryByRole("button", { name: /live$/ }),
      ).not.toBeInTheDocument();
    });

    it("shows a Move override with the Move's text when the run started", async () => {
      apiClient.getEvalRun.mockResolvedValue({
        ...comparison,
        variants: [
          comparison.variants[0],
          {
            letter: "B",
            setting_overrides: {
              "move:m-1": {
                name: "Research",
                when_it_fits: "They need options found.",
                how_to_do_it: "Find three options.",
              },
            },
            made_live: null,
          },
        ],
      });
      renderWithQueries(<EvalRunView runId="run-1" />);

      const variantB = await screen.findByRole("region", { name: "Variant B" });
      expect(
        await within(variantB).findByText("Move: Research"),
      ).toBeInTheDocument();
      expect(
        within(variantB).getByText("Live when it started:").parentElement,
      ).toHaveTextContent("How to do it: Search and compare.");
      expect(
        within(variantB).getByText("Variant B:").parentElement,
      ).toHaveTextContent("How to do it: Find three options.");
    });

    it("makes a Variant live in one click when nothing changed since", async () => {
      apiClient.getEvalRun.mockResolvedValue(comparison);
      apiClient.listLiveChanges.mockResolvedValue([]);
      apiClient.makeVariantLive.mockResolvedValue({
        ...comparison.variants[1],
        made_live: {
          by_name: "Owner",
          at: "2026-11-15T10:00:00Z",
          applied_keys: ["understanding_thinking"],
          left_out_keys: [],
        },
      });
      renderWithQueries(<EvalRunView runId="run-1" />);

      await userEvent.click(
        await screen.findByRole("button", { name: "Make Variant B live" }),
      );

      expect(apiClient.listLiveChanges).toHaveBeenCalledWith("run-1", "B");
      expect(apiClient.makeVariantLive).toHaveBeenCalledWith("run-1", "B", []);
    });

    it("asks to confirm or leave out a setting changed live since the run", async () => {
      const twoChanges = {
        ...comparison,
        variants: [
          comparison.variants[0],
          {
            letter: "B",
            setting_overrides: {
              understanding_thinking: false,
              daily_message_limit: 80,
            },
            made_live: null,
          },
        ],
      };
      apiClient.getEvalRun.mockResolvedValue(twoChanges);
      apiClient.listLiveChanges.mockResolvedValue([
        {
          key: "understanding_thinking",
          then: true,
          now: false,
          override: false,
        },
        { key: "daily_message_limit", then: 50, now: 60, override: 80 },
      ]);
      apiClient.makeVariantLive.mockResolvedValue({
        ...twoChanges.variants[1],
        made_live: null,
      });
      renderWithQueries(<EvalRunView runId="run-1" />);

      await userEvent.click(
        await screen.findByRole("button", { name: "Make Variant B live" }),
      );

      const confirm = await screen.findByRole("region", {
        name: "Confirm making Variant B live",
      });
      expect(apiClient.makeVariantLive).not.toHaveBeenCalled();
      const limitChange = within(confirm).getByRole("checkbox", {
        name: /daily_message_limit/,
      });
      expect(limitChange.closest("label")).toHaveTextContent(
        "When the run started: 50Live now: 60Variant B: 80",
      );
      await userEvent.click(limitChange);
      await userEvent.click(
        within(confirm).getByRole("button", { name: "Make live" }),
      );

      expect(apiClient.makeVariantLive).toHaveBeenCalledWith("run-1", "B", [
        "daily_message_limit",
      ]);
    });

    it("shows who made a Variant live, when, and what was applied or left out", async () => {
      apiClient.getEvalRun.mockResolvedValue({
        ...comparison,
        variants: [
          comparison.variants[0],
          {
            ...comparison.variants[1],
            made_live: {
              by_name: "Maya Lin",
              at: "2026-11-15T10:00:00Z",
              applied_keys: ["understanding_thinking"],
              left_out_keys: ["daily_message_limit"],
            },
          },
        ],
      });
      renderWithQueries(<EvalRunView runId="run-1" />);

      const variantB = await screen.findByRole("region", { name: "Variant B" });
      expect(
        await within(variantB).findByText("Applied: Understanding thinking."),
      ).toBeInTheDocument();
      expect(
        within(variantB).getByText(/Made live by Maya Lin/),
      ).toBeInTheDocument();
      expect(
        within(variantB).getByText(/Left out.*daily_message_limit/),
      ).toBeInTheDocument();
      expect(
        within(variantB).queryByRole("button", { name: "Make Variant B live" }),
      ).not.toBeInTheDocument();
    });

    it("offers Make Live only once the run has finished", async () => {
      apiClient.getEvalRun.mockResolvedValue({
        ...comparison,
        state: "cancelled",
      });
      renderWithQueries(<EvalRunView runId="run-1" />);

      expect(
        await screen.findByRole("region", { name: "Variant B" }),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Make Variant B live" }),
      ).not.toBeInTheDocument();
    });
  });
});
