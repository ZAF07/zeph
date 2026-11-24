import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PatternCatalog } from "@/components/PatternCatalog";
import type { ApiClient, PatternType } from "@/lib/api-client";
import { patternType } from "@/test/pattern-type";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getPatternCatalog: vi.fn<ApiClient["getPatternCatalog"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

const approvedType: PatternType = {
  ...patternType,
  id: "ACH.WORTH.PERF",
  area: "achievement",
  name: "Performance-contingent self-worth",
  version: "1.0.0",
  status: "approved",
  approved_by: "Zaf",
  approved_on: "2026-11-24",
  exclusions: [],
  other_versions: [],
};

/**
 * Finds one group of an open card by its heading.
 *
 * @param card - The card.
 * @param name - The group's heading.
 * @returns Queries inside the group.
 */
function groupOf(card: HTMLElement, name: string) {
  return within(within(card).getByRole("group", { name }));
}

describe("PatternCatalog", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getPatternCatalog.mockResolvedValue([patternType, approvedType]);
  });

  it("lists every Pattern Type with its area, status and version", async () => {
    renderWithQueries(<PatternCatalog />);

    const first = await screen.findByRole("region", {
      name: "Conflict avoidance to preserve belonging",
    });
    const second = screen.getByRole("region", {
      name: "Performance-contingent self-worth",
    });
    const firstRow = within(first).getByRole("button", { expanded: true });
    expect(firstRow).toHaveTextContent(
      "Disagreement with a valued other → Withholds or softens own view → To protect belonging",
    );
    expect(firstRow).toHaveTextContent("Conflict");
    expect(firstRow).toHaveTextContent("Draft");
    expect(firstRow).toHaveTextContent("v0.2.0");
    const secondRow = within(second).getByRole("button", { expanded: false });
    expect(secondRow).toHaveTextContent("Achievement");
    expect(secondRow).toHaveTextContent("Approved");
    expect(secondRow).toHaveTextContent("v1.0.0");
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText(/Pattern Types$/)).toBeInTheDocument();
  });

  it("shows all of a Pattern Type's details in its open card", async () => {
    renderWithQueries(<PatternCatalog />);

    const card = await screen.findByRole("region", {
      name: "Conflict avoidance to preserve belonging",
    });
    const what = groupOf(card, "What it is");
    expect(what.getByText("CONF.AVOID.BELONG")).toBeVisible();
    expect(
      what.getByText(
        "The person dilutes their own position to keep the peace.",
      ),
    ).toBeVisible();
    expect(what.getByText("Disagreement with a valued other")).toBeVisible();
    expect(what.getByText("Withholds or softens own view")).toBeVisible();
    expect(what.getByText("To protect belonging")).toBeVisible();
    expect(
      what.getByText("Young's subjugation schema; Anxious attachment (ECR-R)"),
    ).toBeVisible();

    const signs = groupOf(card, "Signs");
    expect(
      signs.getByText("Apologises or hedges before stating a need"),
    ).toBeVisible();
    expect(signs.getByText("I1")).toBeVisible();
    expect(signs.getByText("Moderate")).toBeVisible();
    expect(signs.getByText("Behaviour")).toBeVisible();

    const against = groupOf(card, "Signs against");
    expect(
      against.getByText("States disagreement directly with close others"),
    ).toBeVisible();
    expect(against.getByText("Strong")).toBeVisible();
    expect(against.getByText("What goes on inside")).toBeVisible();

    const lookAlikes = groupOf(card, "Look-alikes");
    expect(
      lookAlikes.getByText("Performance-contingent self-worth"),
    ).toBeVisible();
    expect(lookAlikes.getByText("ACH.WORTH.PERF")).toBeVisible();
    expect(
      lookAlikes.getByText("Avoids conflict because criticism means failure"),
    ).toBeVisible();
    expect(lookAlikes.getByText("Plain politeness")).toBeVisible();
    expect(lookAlikes.getByText("Not a Pattern Type")).toBeVisible();
    expect(lookAlikes.getByText("What anyone would do")).toBeVisible();
    expect(
      lookAlikes.getByText("Low-stakes avoidance with strangers"),
    ).toBeVisible();

    const exclusions = groupOf(card, "Exclusions");
    expect(exclusions.getByText("Grief")).toBeVisible();
    expect(exclusions.getByText("Evidence ignored")).toBeVisible();
    expect(exclusions.getByText("Job loss in the last month")).toBeVisible();
    expect(exclusions.getByText("Counted, not shared")).toBeVisible();

    const wording = groupOf(card, "Wording");
    expect(wording.getByText("You seem to protect closeness.")).toBeVisible();
    expect(
      wording.getByText("Next time {person} asks, notice what you say."),
    ).toBeVisible();

    const status = groupOf(card, "Numbers and status");
    expect(status.getByText("3 needed")).toBeVisible();
    expect(status.getByText("0.2")).toBeVisible();
    expect(
      status.getByText("Draft. Gathers evidence, never shared."),
    ).toBeVisible();
    expect(status.getByText(/^0\.2\.0, loaded 24 Nov 2026$/)).toBeVisible();
    expect(status.getByText("0.1.0")).toBeVisible();
  });

  it("shows who approved a Pattern Type, and says when parts are empty", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PatternCatalog />);

    const card = await screen.findByRole("region", {
      name: "Performance-contingent self-worth",
    });
    await user.click(within(card).getByRole("button", { expanded: false }));

    expect(
      groupOf(card, "Numbers and status").getByText(
        "Approved by Zaf on 24 Nov 2026. May be shared once ready.",
      ),
    ).toBeVisible();
    expect(
      groupOf(card, "Numbers and status").getByText("No other versions"),
    ).toBeVisible();
    expect(groupOf(card, "Exclusions").getByText("None")).toBeVisible();
  });

  it("opens and folds every card with Expand all and Collapse all", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PatternCatalog />);
    await screen.findByRole("region", {
      name: "Performance-contingent self-worth",
    });

    await user.click(screen.getByRole("button", { name: "Expand all" }));
    expect(screen.getAllByRole("button", { expanded: true })).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: "Collapse all" }));
    expect(screen.queryAllByRole("button", { expanded: true })).toHaveLength(0);
  });

  it("gives no way to edit, add or remove a Pattern Type", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PatternCatalog />);
    await screen.findByRole("region", {
      name: "Performance-contingent self-worth",
    });
    await user.click(screen.getByRole("button", { name: "Expand all" }));

    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
    expect(screen.queryAllByRole("combobox")).toHaveLength(0);
    expect(screen.queryAllByRole("switch")).toHaveLength(0);
    expect(
      screen.getAllByRole("button").map((button) => button.textContent),
    ).toEqual([
      "Expand all",
      "Collapse all",
      expect.stringContaining("Conflict avoidance to preserve belonging"),
      expect.stringContaining("Performance-contingent self-worth"),
    ]);
    expect(screen.getByText("Read only")).toBeVisible();
  });

  it("says so when there are no Pattern Types", async () => {
    apiClient.getPatternCatalog.mockResolvedValue([]);
    renderWithQueries(<PatternCatalog />);

    expect(await screen.findByText("No Pattern Types yet")).toBeVisible();
  });

  it("shows an error with a retry when the catalog can't be loaded", async () => {
    const user = userEvent.setup();
    apiClient.getPatternCatalog.mockRejectedValueOnce(new Error("down"));
    renderWithQueries(<PatternCatalog />);

    expect(
      await screen.findByText("Couldn’t load the Pattern Catalog"),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("region", {
        name: "Conflict avoidance to preserve belonging",
      }),
    ).toBeVisible();
  });
});
