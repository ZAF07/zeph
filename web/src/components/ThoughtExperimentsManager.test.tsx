import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ThoughtExperimentsManager } from "@/components/ThoughtExperimentsManager";
import {
  ApiError,
  type ApiClient,
  type ThoughtExperiment,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listThoughtExperiments: vi.fn<ApiClient["listThoughtExperiments"]>(),
  addThoughtExperiment: vi.fn<ApiClient["addThoughtExperiment"]>(),
  updateThoughtExperiment: vi.fn<ApiClient["updateThoughtExperiment"]>(),
  archiveThoughtExperiment: vi.fn<ApiClient["archiveThoughtExperiment"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const BELONG = "CONF.AVOID.BELONG";
const WORTH = "ACH.WORTH.PERF";
const PLAN = "CTRL.UNCERT.PLAN";

function thoughtExperiment(
  id: string,
  pair: [string, string],
  overrides: Partial<ThoughtExperiment> = {},
): ThoughtExperiment {
  return {
    id,
    wording: `What would you do, ${id}?`,
    pattern_type_id: pair[0],
    other_pattern_type_id: pair[1],
    sensitivity: "low",
    starter: false,
    on: true,
    archived_at: null,
    asked_count: 0,
    ...overrides,
  };
}

const teamPlan = thoughtExperiment("team-plan", [BELONG, WORTH], {
  starter: true,
  asked_count: 4,
});
const holiday = thoughtExperiment("holiday", [BELONG, PLAN], {
  on: false,
  sensitivity: "medium",
});
const oldOne = thoughtExperiment("old-one", [WORTH, PLAN], {
  archived_at: "2026-11-20T10:00:00Z",
  asked_count: 1,
});

async function openCard(name: string): Promise<ReturnType<typeof within>> {
  await screen.findAllByRole("button", { name: "Expand all" });
  for (const expandAll of screen.getAllByRole("button", {
    name: "Expand all",
  })) {
    fireEvent.click(expandAll);
  }
  return within(await screen.findByRole("region", { name }));
}

const leadingRefusal = new ApiError(
  422,
  "/api/admin/thought-experiments",
  "This wording may lead them to an answer. Change it, or save it anyway.",
  {
    leading:
      "“Surely” suggests the answer. Ask what they would do, and leave both choices open.",
  },
);

describe("ThoughtExperimentsManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listThoughtExperiments.mockResolvedValue({
      thought_experiments: [teamPlan, holiday, oldOne],
      pattern_types: [
        { id: WORTH, name: "Performance-contingent self-worth" },
        { id: BELONG, name: "Softening disagreement to protect belonging" },
        { id: PLAN, name: "Control-seeking under uncertainty" },
      ],
    });
  });

  it("lists each with its pair, tags and times asked, archived ones apart", async () => {
    renderWithQueries(<ThoughtExperimentsManager />);

    const card = await openCard(`${BELONG} or ${WORTH}`);
    expect(
      card.getByRole("button", { name: new RegExp(`^${BELONG}`) }),
    ).toHaveTextContent("Starter4 times asked");
    expect(card.getByLabelText("Wording")).toHaveValue(teamPlan.wording);
    expect(card.getByLabelText("Pattern Type")).toHaveValue(BELONG);
    expect(card.getByLabelText("Its look-alike")).toHaveValue(WORTH);
    expect(card.getByLabelText("Sensitivity")).toHaveValue("low");
    expect(card.getByRole("switch", { name: "Starter" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(card.getByRole("switch", { name: "On" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(card.getByText(/One of the two look-alikes/)).toBeInTheDocument();
    const off = await openCard(`${BELONG} or ${PLAN}`);
    expect(
      off.getByRole("button", { name: new RegExp(`^${BELONG}`) }),
    ).toHaveTextContent("Off");
    expect(
      screen.getByText("Thought Experiments", { exact: false }),
    ).toHaveTextContent("2 Thought Experiments");
    const archived = await openCard(`${WORTH} or ${PLAN}`);
    expect(archived.queryByLabelText("Wording")).not.toBeInTheDocument();
    expect(
      archived.getByText(
        "Archived: Zeph never asks it again. Past tries still show it.",
      ),
    ).toBeInTheDocument();
  });

  it("saves an edit, switching it off", async () => {
    const user = userEvent.setup();
    apiClient.updateThoughtExperiment.mockResolvedValue({
      ...teamPlan,
      on: false,
    });
    renderWithQueries(<ThoughtExperimentsManager />);
    const card = await openCard(`${BELONG} or ${WORTH}`);

    await user.click(card.getByRole("switch", { name: "On" }));
    await user.selectOptions(card.getByLabelText("Sensitivity"), "high");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateThoughtExperiment).toHaveBeenCalledWith(
      "team-plan",
      {
        wording: teamPlan.wording,
        pattern_type_id: BELONG,
        other_pattern_type_id: WORTH,
        sensitivity: "high",
        starter: true,
        on: false,
      },
      false,
    );
    expect(
      await screen.findByText("Saved the Thought Experiment."),
    ).toBeInTheDocument();
  });

  it("warns about leading wording and saves it anyway when asked", async () => {
    const user = userEvent.setup();
    apiClient.updateThoughtExperiment
      .mockRejectedValueOnce(leadingRefusal)
      .mockResolvedValueOnce(teamPlan);
    renderWithQueries(<ThoughtExperimentsManager />);
    const card = await openCard(`${BELONG} or ${WORTH}`);

    await user.clear(card.getByLabelText("Wording"));
    await user.type(card.getByLabelText("Wording"), "Surely you would say so?");
    await user.click(card.getByRole("button", { name: "Save" }));

    const warning = await card.findByRole("alertdialog", {
      name: "Leading wording",
    });
    expect(warning).toHaveTextContent("“Surely” suggests the answer.");
    await user.click(
      within(warning).getByRole("button", { name: "Save anyway" }),
    );
    expect(apiClient.updateThoughtExperiment).toHaveBeenLastCalledWith(
      "team-plan",
      expect.objectContaining({ wording: "Surely you would say so?" }),
      true,
    );
  });

  it("goes back to editing from the warning without saving", async () => {
    const user = userEvent.setup();
    apiClient.updateThoughtExperiment.mockRejectedValueOnce(leadingRefusal);
    renderWithQueries(<ThoughtExperimentsManager />);
    const card = await openCard(`${BELONG} or ${WORTH}`);

    await user.type(card.getByLabelText("Wording"), " Surely?");
    await user.click(card.getByRole("button", { name: "Save" }));
    await user.click(await card.findByRole("button", { name: "Keep editing" }));

    expect(card.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(card.getByRole("button", { name: "Save" })).toBeEnabled();
    expect(apiClient.updateThoughtExperiment).toHaveBeenCalledTimes(1);
  });

  it("archives one after confirming", async () => {
    const user = userEvent.setup();
    apiClient.archiveThoughtExperiment.mockResolvedValue({
      ...teamPlan,
      archived_at: "2026-11-24T10:00:00Z",
    });
    renderWithQueries(<ThoughtExperimentsManager />);
    const card = await openCard(`${BELONG} or ${WORTH}`);

    await user.click(card.getByRole("button", { name: "Archive" }));
    const confirm = card.getByRole("alertdialog", {
      name: "Archive this Thought Experiment?",
    });
    expect(confirm).toHaveTextContent("Past tries still show it.");
    await user.click(within(confirm).getByRole("button", { name: "Archive" }));

    expect(apiClient.archiveThoughtExperiment).toHaveBeenCalledWith(
      "team-plan",
    );
  });

  it("adds one with two different Pattern Types from the catalog", async () => {
    const user = userEvent.setup();
    apiClient.addThoughtExperiment.mockResolvedValue(teamPlan);
    renderWithQueries(<ThoughtExperimentsManager />);
    await user.click(
      await screen.findByRole("button", { name: "Add a Thought Experiment" }),
    );
    const box = within(
      screen.getByRole("region", { name: "New Thought Experiment" }),
    );
    const add = box.getByRole("button", { name: "Add" });

    await user.type(box.getByLabelText("Wording"), "What do you tell them?");
    await user.selectOptions(box.getByLabelText("Pattern Type"), BELONG);
    await user.selectOptions(box.getByLabelText("Its look-alike"), BELONG);
    expect(add).toBeDisabled();
    await user.selectOptions(box.getByLabelText("Its look-alike"), PLAN);
    await user.click(add);

    expect(apiClient.addThoughtExperiment).toHaveBeenCalledWith(
      {
        wording: "What do you tell them?",
        pattern_type_id: BELONG,
        other_pattern_type_id: PLAN,
        sensitivity: "low",
        starter: false,
        on: true,
      },
      false,
    );
  });

  it("shows the empty state with none", async () => {
    apiClient.listThoughtExperiments.mockResolvedValue({
      thought_experiments: [],
      pattern_types: [],
    });
    renderWithQueries(<ThoughtExperimentsManager />);

    expect(
      await screen.findByText("No Thought Experiments"),
    ).toBeInTheDocument();
  });
});
