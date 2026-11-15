import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EvalRunsList } from "@/components/EvalRunsList";
import type { ApiClient, EvalRun } from "@/lib/api-client";
import { finishedRun } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listEvalRuns: vi.fn<ApiClient["listEvalRuns"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const dashboardRun: EvalRun = {
  ...finishedRun,
  evals: ["safeguard", "persona"],
  passed: 29,
  failed: 1,
  errored: 1,
  tokens_in: 40000,
  tokens_out: 2000,
};
const terminalRun: EvalRun = {
  ...finishedRun,
  id: "run-2",
  started_from: "terminal",
  started_by_name: null,
  state: "running",
};

describe("EvalRunsList", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listEvalRuns.mockImplementation((includeTerminal) =>
      Promise.resolve(
        includeTerminal ? [terminalRun, dashboardRun] : [dashboardRun],
      ),
    );
  });

  it("lists Dashboard runs with who started them, their Evals and results", async () => {
    renderWithQueries(<EvalRunsList />);

    const table = await screen.findByRole("table");
    const [, row] = within(table).getAllByRole("row");
    const cells = within(row).getAllByRole("cell");
    expect(cells.slice(1).map((cell) => cell.textContent)).toEqual([
      "Owner",
      "Safeguard, Persona",
      "Finished",
      "29 passed · 1 failed · 1 error",
      "40,000 in / 2,000 out",
    ]);
    expect(within(cells[0]).getByRole("link")).toHaveAttribute(
      "href",
      "/admin/evals/runs/run-1",
    );
    expect(apiClient.listEvalRuns).toHaveBeenCalledWith(false);
    expect(screen.getByRole("link", { name: "New run" })).toHaveAttribute(
      "href",
      "/admin/evals/new",
    );
  });

  it("shows terminal runs only once the toggle is on", async () => {
    renderWithQueries(<EvalRunsList />);
    await screen.findByRole("table");
    expect(screen.queryByText("Terminal")).not.toBeInTheDocument();

    const toggle = screen.getByRole("button", { name: "Show terminal runs" });
    await userEvent.click(toggle);

    expect(await screen.findByText("Terminal")).toBeInTheDocument();
    expect(toggle).toHaveAttribute("aria-pressed", "true");
    expect(apiClient.listEvalRuns).toHaveBeenLastCalledWith(true);
  });

  it("says so when there are no runs yet", async () => {
    apiClient.listEvalRuns.mockResolvedValue([]);

    renderWithQueries(<EvalRunsList />);

    expect(await screen.findByText("No Eval Runs yet")).toBeInTheDocument();
  });
});
