import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NewEvalRunForm } from "@/components/NewEvalRunForm";
import type { ApiClient } from "@/lib/api-client";
import { finishedRun } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listEvals: vi.fn<ApiClient["listEvals"]>(),
  startEvalRun: vi.fn<ApiClient["startEvalRun"]>(),
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

    expect(apiClient.startEvalRun).toHaveBeenCalledWith([
      "safeguard",
      "persona",
    ]);
    expect(router.push).toHaveBeenCalledWith("/admin/evals/runs/run-9");
  });

  it("shows each Eval's cases and can't pick one with none", async () => {
    renderWithQueries(<NewEvalRunForm />);

    expect(
      await screen.findByRole("checkbox", { name: /Knowledge · 0 cases/ }),
    ).toBeDisabled();
    expect(screen.getByText("plan, traffic")).toBeInTheDocument();
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
});
