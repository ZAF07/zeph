import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UnmatchedPatternsManager } from "@/components/UnmatchedPatternsManager";
import {
  ApiError,
  type ApiClient,
  type UnmatchedEntry,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listUnmatchedEntries: vi.fn<ApiClient["listUnmatchedEntries"]>(),
  markUnmatchedEntry: vi.fn<ApiClient["markUnmatchedEntry"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const BELONG = "CONF.AVOID.BELONG";
const patternTypes = [
  { id: "ACH.WORTH.PERF", name: "Performance-contingent self-worth" },
  { id: BELONG, name: "Conflict avoidance to preserve belonging" },
];

function entry(
  id: string,
  description: string,
  overrides: Partial<UnmatchedEntry> = {},
): UnmatchedEntry {
  return {
    id,
    description,
    user_count: 1,
    mark: "to_review",
    folded_into_pattern_type_id: null,
    dropped_before: false,
    ...overrides,
  };
}

const jokes = entry("jokes", "Makes jokes when things get serious", {
  user_count: 4,
});
const absorbed = entry("absorbed", "Lets everything else slip", {
  user_count: 2,
  dropped_before: true,
});

function listOf(...entries: UnmatchedEntry[]) {
  return { entries, pattern_types: patternTypes };
}

async function card(name: string): Promise<ReturnType<typeof within>> {
  return within(await screen.findByRole("region", { name }));
}

describe("UnmatchedPatternsManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClient.listUnmatchedEntries.mockResolvedValue(listOf(jokes, absorbed));
    apiClient.markUnmatchedEntry.mockResolvedValue(jokes);
  });

  it("lists the entries to review with their description and User count", async () => {
    renderWithQueries(<UnmatchedPatternsManager />);

    const first = await card(jokes.description);
    const topRow = first.getByRole("button", { expanded: true });
    expect(topRow).toHaveTextContent("To review");
    expect(topRow).toHaveTextContent("4 Users");
    const second = await card(absorbed.description);
    expect(second.getByText("Back after a drop")).toBeInTheDocument();
    expect(screen.getByText("entries")).toBeInTheDocument();
    expect(apiClient.listUnmatchedEntries).toHaveBeenCalledWith("to_review");
    expect(
      screen.getByRole("button", { name: "To review", pressed: true }),
    ).toBeInTheDocument();
  });

  it("asks for the entries with the mark of the pill chosen", async () => {
    const user = userEvent.setup();
    renderWithQueries(<UnmatchedPatternsManager />);
    await card(jokes.description);
    apiClient.listUnmatchedEntries.mockResolvedValue(listOf());

    await user.click(screen.getByRole("button", { name: "Dropped" }));

    expect(await screen.findByText("No entries here")).toBeInTheDocument();
    expect(apiClient.listUnmatchedEntries).toHaveBeenLastCalledWith("dropped");

    await user.click(screen.getByRole("button", { name: "All" }));

    expect(apiClient.listUnmatchedEntries).toHaveBeenLastCalledWith(null);
  });

  it("says so when there is nothing to review", async () => {
    apiClient.listUnmatchedEntries.mockResolvedValue(listOf());

    renderWithQueries(<UnmatchedPatternsManager />);

    expect(await screen.findByText("Nothing to review")).toBeInTheDocument();
  });

  it("marks an entry as dropped", async () => {
    const user = userEvent.setup();
    renderWithQueries(<UnmatchedPatternsManager />);
    const first = await card(jokes.description);
    expect(first.getByRole("button", { name: "Save" })).toBeDisabled();

    await user.selectOptions(first.getByLabelText("Mark"), "dropped");
    await user.click(first.getByRole("button", { name: "Save" }));

    expect(apiClient.markUnmatchedEntry).toHaveBeenCalledWith(
      "jokes",
      "dropped",
      null,
    );
    expect(await screen.findByText("Saved the mark.")).toBeInTheDocument();
  });

  it("asks which Pattern Type before an entry can be saved as folded", async () => {
    const user = userEvent.setup();
    renderWithQueries(<UnmatchedPatternsManager />);
    const first = await card(jokes.description);
    expect(first.queryByLabelText("Folded into")).not.toBeInTheDocument();

    await user.selectOptions(first.getByLabelText("Mark"), "folded");

    expect(first.getByRole("button", { name: "Save" })).toBeDisabled();

    await user.selectOptions(first.getByLabelText("Folded into"), BELONG);
    await user.click(first.getByRole("button", { name: "Save" }));

    expect(apiClient.markUnmatchedEntry).toHaveBeenCalledWith(
      "jokes",
      "folded",
      BELONG,
    );
  });

  it("shows a folded entry's Pattern Type and discards an unsaved change", async () => {
    const user = userEvent.setup();
    const folded = entry("folded", "Keeps the peace at any cost", {
      mark: "folded",
      folded_into_pattern_type_id: BELONG,
    });
    apiClient.listUnmatchedEntries.mockResolvedValue(listOf(folded));
    renderWithQueries(<UnmatchedPatternsManager />);
    const only = await card(folded.description);
    expect(only.getByText(`Folded into ${BELONG}`)).toBeInTheDocument();
    expect(only.getByLabelText("Folded into")).toHaveValue(BELONG);

    await user.selectOptions(only.getByLabelText("Mark"), "new_pattern_type");

    expect(only.getByText("Unsaved changes")).toBeInTheDocument();

    await user.click(only.getByRole("button", { name: "Discard" }));

    expect(only.getByLabelText("Mark")).toHaveValue("folded");
    expect(only.queryByText("Unsaved changes")).not.toBeInTheDocument();
  });

  it("shows why the backend refused a mark", async () => {
    const user = userEvent.setup();
    apiClient.markUnmatchedEntry.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/unmatched-patterns/jokes/mark",
        "Pick the Pattern Type in the Pattern Catalog it is folded into.",
      ),
    );
    renderWithQueries(<UnmatchedPatternsManager />);
    const first = await card(jokes.description);

    await user.selectOptions(first.getByLabelText("Mark"), "dropped");
    await user.click(first.getByRole("button", { name: "Save" }));

    expect(
      await first.findByText(
        "Pick the Pattern Type in the Pattern Catalog it is folded into.",
      ),
    ).toBeInTheDocument();
  });

  it("offers a retry when the entries can't be loaded", async () => {
    apiClient.listUnmatchedEntries.mockRejectedValue(new Error("down"));

    renderWithQueries(<UnmatchedPatternsManager />);

    expect(
      await screen.findByText("Couldn’t load the unmatched entries"),
    ).toBeInTheDocument();
  });
});
