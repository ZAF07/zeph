import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NewEvalRunForm } from "@/components/NewEvalRunForm";
import type { ApiClient } from "@/lib/api-client";
import { finishedRun } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listEvals: vi.fn<ApiClient["listEvals"]>(),
  startEvalRun: vi.fn<ApiClient["startEvalRun"]>(),
  estimateEvalRun: vi.fn<ApiClient["estimateEvalRun"]>(),
};
const router = { push: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

describe("NewEvalRunForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listEvals.mockResolvedValue([
      { eval: "safeguard", case_keys: ["plan", "traffic"] },
      { eval: "persona", case_keys: ["small-talk"] },
      { eval: "knowledge", case_keys: [] },
    ]);
    apiClient.startEvalRun.mockResolvedValue({
      ...finishedRun,
      id: "run-9",
      state: "queued",
    });
    apiClient.estimateEvalRun.mockResolvedValue({
      case_count: 3,
      rough_case_count: 1,
      tokens_in: 82_000,
      tokens_out: 9_000,
      models: [
        { model: "deepseek-flash", tokens_in: 82_000, tokens_out: 9_000 },
      ],
      cost_sgd: 0.045,
      unpriced_models: [],
    });
  });

  it("starts a run of the ticked Evals and opens its page", async () => {
    renderWithQueries(<NewEvalRunForm />);

    const start = await screen.findByRole("button", { name: "Start run" });
    expect(start).toBeDisabled();
    await userEvent.click(screen.getByRole("checkbox", { name: /Persona/ }));
    await userEvent.click(screen.getByRole("checkbox", { name: /Safeguard/ }));
    await userEvent.click(
      screen.getByRole("button", { name: "Start run · 3 cases" }),
    );

    expect(apiClient.startEvalRun).toHaveBeenCalledWith({
      evals: ["safeguard", "persona"],
      case_keys: [],
    });
    expect(router.push).toHaveBeenCalledWith("/admin/evals/runs/run-9");
  });

  it("shows each Eval's cases and can't pick one with none", async () => {
    renderWithQueries(<NewEvalRunForm />);

    expect(
      await screen.findByRole("checkbox", { name: /Knowledge · 0 cases/ }),
    ).toBeDisabled();
    expect(
      screen.getByRole("checkbox", { name: "traffic" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The Judge checks Zeph’s replies/),
    ).toBeInTheDocument();
  });

  it("says so when the run can't be started", async () => {
    apiClient.startEvalRun.mockRejectedValue(new Error("down"));
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );
    await userEvent.click(screen.getByRole("button", { name: /Start run/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t start the run",
    );
    expect(router.push).not.toHaveBeenCalled();
  });

  it("runs single cases picked inside an Eval", async () => {
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: "traffic" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Start run · 1 case" }),
    );

    expect(apiClient.startEvalRun).toHaveBeenCalledWith({
      evals: [],
      case_keys: ["traffic"],
    });
  });

  it("shows an estimate before starting, saying where it comes from", async () => {
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );

    const estimate = await screen.findByRole("region", { name: "Estimate" });
    expect(
      await within(estimate).findByText(
        "About 82,000 in / 9,000 out tokens · S$0.0450",
      ),
    ).toBeInTheDocument();
    expect(within(estimate).getByText(/1 case never ran/)).toBeInTheDocument();
    expect(apiClient.estimateEvalRun).toHaveBeenLastCalledWith({
      evals: ["safeguard"],
      case_keys: [],
    });
  });

  it("still lets a run start when the estimate fails", async () => {
    apiClient.estimateEvalRun.mockRejectedValue(new Error("down"));
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );

    expect(
      await screen.findByText(/Couldn’t work out an estimate/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Start run · 2 cases" }),
    ).toBeEnabled();
  });
});
