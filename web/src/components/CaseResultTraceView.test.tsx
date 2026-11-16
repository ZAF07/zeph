import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CaseResultTraceView } from "@/components/CaseResultTraceView";
import { ApiError, type ApiClient } from "@/lib/api-client";
import { passedResult } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getCaseResultTrace: vi.fn<ApiClient["getCaseResultTrace"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

describe("CaseResultTraceView", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows the result, then every model call with its full content", async () => {
    apiClient.getCaseResultTrace.mockResolvedValue({
      run_id: "run-1",
      result: passedResult,
      calls: [
        {
          id: "c1",
          step: "understanding",
          model: "deepseek-flash",
          thinking: true,
          started_at: "2026-11-15T09:00:10Z",
          duration_ms: 3300,
          tokens_in: 1800,
          tokens_out: 480,
          error: null,
          tools_called: [],
          content: {
            instructions: "Understand the Message.",
            history: [{ role: "user", text: "I have the pills ready" }],
            tools_offered: [],
            tool_calls: [],
            response: '{"need": "Be heard"}',
            reasoning: null,
          },
          understanding_shape: null,
          check_in_shape: null,
        },
      ],
    });
    renderWithQueries(
      <CaseResultTraceView runId="run-1" resultId="result-1" />,
    );

    expect(
      await screen.findByRole("heading", { name: "Trace of plan" }),
    ).toBeInTheDocument();
    const call = screen.getByRole("article", { name: "Understanding" });
    expect(within(call).getByText("3.3 s")).toBeInTheDocument();
    expect(within(call).getByText("1,800 in / 480 out")).toBeInTheDocument();
    expect(within(call).getByText("Content")).toBeInTheDocument();
    expect(
      screen.getByText(/never show in the Model Call Log/),
    ).toBeInTheDocument();
    expect(apiClient.getCaseResultTrace).toHaveBeenCalledWith(
      "run-1",
      "result-1",
    );
  });

  it("says so when the result is gone", async () => {
    apiClient.getCaseResultTrace.mockRejectedValue(new ApiError(404, "/x"));
    renderWithQueries(<CaseResultTraceView runId="run-1" resultId="gone" />);

    expect(
      await screen.findByText(/This Case Result is gone/),
    ).toBeInTheDocument();
  });
});
