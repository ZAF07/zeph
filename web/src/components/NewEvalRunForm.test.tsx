import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NewEvalRunForm } from "@/components/NewEvalRunForm";
import { ApiError, type ApiClient } from "@/lib/api-client";
import { finishedRun } from "@/test/eval-runs";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listEvals: vi.fn<ApiClient["listEvals"]>(),
  startEvalRun: vi.fn<ApiClient["startEvalRun"]>(),
  estimateEvalRun: vi.fn<ApiClient["estimateEvalRun"]>(),
  listSettingOverrideChoices: vi.fn<ApiClient["listSettingOverrideChoices"]>(),
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
      variants: [
        {
          letter: "A",
          tokens_in: 82_000,
          tokens_out: 9_000,
          cost_sgd: 0.045,
          unpriced_models: [],
        },
      ],
    });
    apiClient.listSettingOverrideChoices.mockResolvedValue({
      settings: [
        {
          key: "understanding_thinking",
          label: "Understanding thinking",
          kind: "on_off",
          minimum: 0,
          maximum: 0,
          max_length: 20000,
          hint: "",
          value: true,
        },
        {
          key: "crisis_reply",
          label: "Crisis Reply",
          kind: "text",
          minimum: 0,
          maximum: 0,
          max_length: 20000,
          hint: "",
          value: "Please reach out. {helplines}",
        },
      ],
      needs: [
        {
          key: "need:n-1",
          name: "Be heard",
          value: {
            name: "Be heard",
            when_it_fits: "They are venting.",
            how_to_reply: "Listen first.",
          },
        },
      ],
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
      models: ["deepseek-flash"],
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
      variants: [{}],
      repeats: 1,
    });
    expect(router.push).toHaveBeenCalledWith("/admin/evals/runs/run-9");
  });

  it("offers the Move Outcome Eval with what it checks", async () => {
    apiClient.listEvals.mockResolvedValue([
      { eval: "move_outcome", case_keys: ["hosting-research-helped"] },
    ]);
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Move Outcome · 1 case/ }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Start run · 1 case" }),
    );

    expect(
      screen.getByText(/leaves the right Move Outcomes/),
    ).toBeInTheDocument();
    expect(apiClient.startEvalRun).toHaveBeenCalledWith({
      evals: ["move_outcome"],
      case_keys: [],
      variants: [{}],
      repeats: 1,
    });
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
      variants: [{}],
      repeats: 1,
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
      variants: [{}],
      repeats: 1,
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

  it("compares Variants with their own overrides and Repeats", async () => {
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Add Variant B" }),
    );
    const variantB = screen.getByRole("region", { name: "Variant B" });
    await userEvent.selectOptions(
      within(variantB).getByRole("combobox", {
        name: "Change a setting in Variant B",
      }),
      "understanding_thinking",
    );
    expect(within(variantB).getByText("Live: On")).toBeInTheDocument();
    await userEvent.click(
      within(variantB).getByRole("switch", { name: "Understanding thinking" }),
    );
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: /Repeats/ }),
      "3",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Start run · 12 cases" }),
    );

    expect(apiClient.startEvalRun).toHaveBeenCalledWith({
      evals: ["safeguard"],
      case_keys: [],
      variants: [{}, { understanding_thinking: false }],
      repeats: 3,
    });
  });

  it("changes a Need for one Variant, starting from its live details", async () => {
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );
    await userEvent.selectOptions(
      await screen.findByRole("combobox", {
        name: "Change a setting in Variant A",
      }),
      "need:n-1",
    );
    const whenItFits = screen.getByRole("textbox", {
      name: "Need: Be heard when it fits",
    });
    expect(whenItFits).toHaveValue("They are venting.");
    await userEvent.clear(whenItFits);
    await userEvent.type(whenItFits, "Only when venting.");
    await userEvent.click(screen.getByRole("button", { name: /Start run/ }));

    expect(apiClient.startEvalRun).toHaveBeenCalledWith(
      expect.objectContaining({
        variants: [
          {
            "need:n-1": {
              name: "Be heard",
              when_it_fits: "Only when venting.",
              how_to_reply: "Listen first.",
            },
          },
        ],
      }),
    );
  });

  it("changes a Move's text for one Variant, starting from its live text", async () => {
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );
    await userEvent.selectOptions(
      await screen.findByRole("combobox", {
        name: "Change a setting in Variant A",
      }),
      "move:m-1",
    );
    const howToDoIt = screen.getByRole("textbox", {
      name: "Move: Research how to do it",
    });
    expect(howToDoIt).toHaveValue("Search and compare.");
    await userEvent.clear(howToDoIt);
    await userEvent.type(howToDoIt, "Find three options.");
    await userEvent.click(screen.getByRole("button", { name: /Start run/ }));

    expect(apiClient.startEvalRun).toHaveBeenCalledWith(
      expect.objectContaining({
        variants: [
          {
            "move:m-1": {
              name: "Research",
              when_it_fits: "They need options found.",
              how_to_do_it: "Find three options.",
            },
          },
        ],
      }),
    );
  });

  it("shows why an override was refused, as the settings page would", async () => {
    apiClient.startEvalRun.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/eval-runs",
        "The Crisis Reply must include {helplines}, where the Helplines go.",
      ),
    );
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );
    await userEvent.selectOptions(
      await screen.findByRole("combobox", {
        name: "Change a setting in Variant A",
      }),
      "crisis_reply",
    );
    await userEvent.clear(
      screen.getByRole("textbox", { name: "Crisis Reply" }),
    );
    await userEvent.type(
      screen.getByRole("textbox", { name: "Crisis Reply" }),
      "Stay safe.",
    );
    await userEvent.click(screen.getByRole("button", { name: /Start run/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t start the run: The Crisis Reply must include {helplines}",
    );
  });

  it("shows each Variant's estimate when comparing", async () => {
    apiClient.estimateEvalRun.mockResolvedValue({
      case_count: 4,
      rough_case_count: 0,
      tokens_in: 20_000,
      tokens_out: 2_000,
      models: [],
      cost_sgd: 0.01,
      unpriced_models: [],
      variants: ["A", "B"].map((letter) => ({
        letter,
        tokens_in: 10_000,
        tokens_out: 1_000,
        cost_sgd: 0.005,
        unpriced_models: [],
      })),
    });
    renderWithQueries(<NewEvalRunForm />);

    await userEvent.click(
      await screen.findByRole("checkbox", { name: /Safeguard/ }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Add Variant B" }),
    );

    const estimate = await screen.findByRole("region", { name: "Estimate" });
    expect(
      await within(estimate).findByText(
        "Variant B: about 10,000 in / 1,000 out tokens · S$0.0050",
      ),
    ).toBeInTheDocument();
    expect(apiClient.estimateEvalRun).toHaveBeenLastCalledWith(
      expect.objectContaining({ variants: [{}, {}] }),
    );
  });
});
