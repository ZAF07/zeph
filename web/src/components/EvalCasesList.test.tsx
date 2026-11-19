import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EvalCasesList } from "@/components/EvalCasesList";
import { ApiError, type ApiClient } from "@/lib/api-client";
import { smallTalkCase } from "@/test/eval-cases";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listEvalCases: vi.fn<ApiClient["listEvalCases"]>(),
  duplicateEvalCase: vi.fn<ApiClient["duplicateEvalCase"]>(),
  archiveEvalCase: vi.fn<ApiClient["archiveEvalCase"]>(),
};
const router = { push: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

/**
 * The table's body rows, one per case.
 *
 * @returns The rows.
 */
async function caseRows(): Promise<HTMLElement[]> {
  const table = await screen.findByRole("table");
  return within(table).getAllByRole("row").slice(1);
}

describe("EvalCasesList", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listEvalCases.mockResolvedValue([
      smallTalkCase,
      {
        ...smallTalkCase,
        key: "are-you-human",
        edited: true,
        updated_by_name: "Owner",
      },
      { ...smallTalkCase, key: "old-case", archived: true },
    ]);
  });

  it("lists the Eval's cases with whether each was edited or archived", async () => {
    renderWithQueries(<EvalCasesList evalName="persona" />);

    const rows = await caseRows();
    expect(
      rows.map((row) => within(row).getAllByRole("link")[0].textContent),
    ).toEqual(["small-talk", "are-you-human", "old-case"]);
    expect(
      within(rows[0]).getByText("From the seed files"),
    ).toBeInTheDocument();
    expect(within(rows[1]).getByText("Edited")).toBeInTheDocument();
    expect(within(rows[1]).getByText(/by Owner/)).toBeInTheDocument();
    expect(within(rows[2]).getByText("Archived")).toBeInTheDocument();
    expect(
      within(rows[2]).queryByRole("button", { name: "Archive" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Add case" })).toHaveAttribute(
      "href",
      "/admin/evals/cases/persona/new",
    );
    expect(apiClient.listEvalCases).toHaveBeenCalledWith("persona");
  });

  it("also shows each case as a card of label and value lines for phones", async () => {
    renderWithQueries(<EvalCasesList evalName="persona" />);
    await caseRows();

    const lines = screen
      .getAllByRole("term")
      .map((term) => `${term.textContent}: ${term.nextSibling?.textContent}`);
    expect(lines.slice(0, 4)).toEqual([
      "Case: small-talk",
      "Status: —",
      "Changed: From the seed files",
      "Actions: EditDuplicateArchive",
    ]);
  });

  it("says the case wasn't archived when archiving fails", async () => {
    apiClient.archiveEvalCase.mockRejectedValue(new Error("down"));
    renderWithQueries(<EvalCasesList evalName="persona" />);

    const [first] = await caseRows();
    await userEvent.click(
      within(first).getByRole("button", { name: "Archive" }),
    );
    await userEvent.click(
      within(screen.getByRole("alertdialog")).getByRole("button", {
        name: "Archive",
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t archive the case. Try again.",
    );
  });

  it("archives a case only after confirming", async () => {
    apiClient.archiveEvalCase.mockResolvedValue({
      ...smallTalkCase,
      archived: true,
    });
    renderWithQueries(<EvalCasesList evalName="persona" />);

    const [first] = await caseRows();
    await userEvent.click(
      within(first).getByRole("button", { name: "Archive" }),
    );
    expect(apiClient.archiveEvalCase).not.toHaveBeenCalled();
    const confirm = screen.getByRole("alertdialog", {
      name: "Archive small-talk?",
    });
    expect(within(confirm).getByText(/New runs leave it out/)).toBeVisible();
    await userEvent.click(
      within(confirm).getByRole("button", { name: "Archive" }),
    );

    expect(apiClient.archiveEvalCase).toHaveBeenCalledWith("small-talk");
  });

  it("duplicates a case under a new key and opens the copy", async () => {
    apiClient.duplicateEvalCase
      .mockRejectedValueOnce(
        new ApiError(422, "/api/admin/eval-cases/small-talk/duplicate", "No", {
          key: "Another case has this key.",
        }),
      )
      .mockResolvedValueOnce({ ...smallTalkCase, key: "small-talk-2" });
    renderWithQueries(<EvalCasesList evalName="persona" />);

    const [first] = await caseRows();
    await userEvent.click(
      within(first).getByRole("button", { name: "Duplicate" }),
    );
    const dialog = within(
      screen.getByRole("dialog", { name: "Duplicate small-talk" }),
    );
    const key = dialog.getByRole("textbox", { name: "Key for the copy" });
    expect(key).toHaveValue("small-talk-copy");
    await userEvent.click(dialog.getByRole("button", { name: "Duplicate" }));
    expect(await dialog.findByRole("alert")).toHaveTextContent(
      "Another case has this key.",
    );
    await userEvent.clear(key);
    await userEvent.type(key, "small-talk-2");
    await userEvent.click(dialog.getByRole("button", { name: "Duplicate" }));

    expect(apiClient.duplicateEvalCase).toHaveBeenLastCalledWith(
      "small-talk",
      "small-talk-2",
    );
    expect(router.push).toHaveBeenCalledWith(
      "/admin/evals/cases/persona/edit/small-talk-2",
    );
  });
});
