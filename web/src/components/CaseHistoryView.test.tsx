import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CaseHistoryView } from "@/components/CaseHistoryView";
import { ApiError, type ApiClient } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getCaseHistory: vi.fn<ApiClient["getCaseHistory"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const entry = {
  run_id: "run-3",
  run_queued_at: "2026-11-15T09:00:00Z",
  result_id: "result-3",
  variant: "A",
  try_number: 1,
  outcome: "pass" as const,
  case_changed: false,
  changed_settings: [],
};

describe("CaseHistoryView", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("lists recent results and marks where the case or settings changed", async () => {
    apiClient.getCaseHistory.mockResolvedValue({
      case: {
        key: "traffic",
        eval: "safeguard",
        content: { kind: "false_alarm" },
        archived: false,
      },
      entries: [
        { ...entry, changed_settings: ["persona", "judge.model"] },
        {
          ...entry,
          run_id: "run-2",
          result_id: "result-2",
          outcome: "fail",
          case_changed: true,
        },
        { ...entry, run_id: "run-1", result_id: "result-1" },
      ],
    });
    renderWithQueries(<CaseHistoryView caseKey="traffic" />);

    expect(
      await screen.findByRole("heading", { name: "traffic" }),
    ).toBeInTheDocument();
    const marks = screen.getAllByText(/^Changed since the run below/);
    expect(marks.map((mark) => mark.textContent)).toEqual([
      "Changed since the run below: 2 settings changed: persona, judge.model",
      "Changed since the run below: Case changed",
    ]);
    expect(screen.getByText("Fail")).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "Full trace" })[1],
    ).toHaveAttribute("href", "/admin/evals/runs/run-2/results/result-2");
  });

  it("says so when there is no such case", async () => {
    apiClient.getCaseHistory.mockRejectedValue(new ApiError(404, "/x"));
    renderWithQueries(<CaseHistoryView caseKey="nope" />);

    expect(
      await screen.findByText("There’s no case named nope."),
    ).toBeInTheDocument();
  });
});
