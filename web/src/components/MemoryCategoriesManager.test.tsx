import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MemoryCategoriesManager } from "@/components/MemoryCategoriesManager";
import {
  ApiError,
  type ApiClient,
  type MemoryCategoryOverview,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listMemoryCategories: vi.fn<ApiClient["listMemoryCategories"]>(),
  addMemoryCategory: vi.fn<ApiClient["addMemoryCategory"]>(),
  updateMemoryCategory: vi.fn<ApiClient["updateMemoryCategory"]>(),
  archiveMemoryCategory: vi.fn<ApiClient["archiveMemoryCategory"]>(),
  restoreMemoryCategory: vi.fn<ApiClient["restoreMemoryCategory"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function category(
  id: string,
  name: string,
  overrides: Partial<MemoryCategoryOverview> = {},
): MemoryCategoryOverview {
  return {
    id,
    name,
    description: `About ${name}`,
    always_include: false,
    archived: false,
    item_count: 3,
    ...overrides,
  };
}

const goals = category("goals", "Goals", { item_count: 97 });
const values = category("values", "Values & beliefs", {
  always_include: true,
});
const habits = category("habits", "Habits (old)", {
  archived: true,
  item_count: 23,
});

async function findCard(name: string): Promise<ReturnType<typeof within>> {
  await screen.findAllByRole("button", { name: "Expand all" });
  for (const expandAll of screen.getAllByRole("button", {
    name: "Expand all",
  })) {
    fireEvent.click(expandAll);
  }
  return within(await screen.findByRole("region", { name }));
}

function cardToggle(card: ReturnType<typeof within>, name: string) {
  return card.getByRole("button", { name: new RegExp(`^${name}`) });
}

describe("MemoryCategoriesManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listMemoryCategories.mockResolvedValue([goals, values, habits]);
  });

  it("lists active and archived categories with their item counts", async () => {
    renderWithQueries(<MemoryCategoriesManager />);

    const goalsCard = await findCard("Goals");
    expect(cardToggle(goalsCard, "Goals")).toHaveTextContent(
      "GoalsAbout Goals97 items",
    );
    expect(
      screen.getByText("active categories", { exact: false }),
    ).toHaveTextContent("2 active categories");
    const valuesCard = await findCard("Values & beliefs");
    expect(cardToggle(valuesCard, "Values")).toHaveTextContent(
      "Always included",
    );
    expect(
      valuesCard.getByRole("switch", {
        name: "Always include Values & beliefs",
      }),
    ).toHaveAttribute("aria-checked", "true");
    expect(
      goalsCard.getByRole("switch", { name: "Always include Goals" }),
    ).toHaveAttribute("aria-checked", "false");
    const habitsCard = await findCard("Habits (old)");
    expect(cardToggle(habitsCard, "Habits")).toHaveTextContent("23 items kept");
    expect(habitsCard.queryByRole("switch")).toBeNull();
    expect(screen.getByText("archived", { exact: false })).toHaveTextContent(
      "1 archived",
    );
    expect(screen.queryByRole("button", { name: /Delete/ })).toBeNull();
  });

  it("shows no archived list when nothing is archived", async () => {
    apiClient.listMemoryCategories.mockResolvedValue([goals]);

    renderWithQueries(<MemoryCategoriesManager />);

    await findCard("Goals");
    expect(screen.getAllByRole("button", { name: "Expand all" })).toHaveLength(
      1,
    );
  });

  it("adds a category and shows it in the list", async () => {
    const user = userEvent.setup();
    const work = category("work", "Work", {
      description: "Job and colleagues",
      item_count: 0,
    });
    apiClient.addMemoryCategory.mockResolvedValue(work);
    renderWithQueries(<MemoryCategoriesManager />);
    await findCard("Goals");
    apiClient.listMemoryCategories.mockResolvedValue([goals, values, work]);

    await user.click(screen.getByRole("button", { name: "Add category" }));
    const box = await findCard("New category");
    await user.type(box.getByLabelText("Name"), "Work");
    await user.type(box.getByLabelText("Description"), "Job and colleagues");
    await user.click(box.getByRole("button", { name: "Add" }));

    expect(apiClient.addMemoryCategory).toHaveBeenCalledWith({
      name: "Work",
      description: "Job and colleagues",
      always_include: false,
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Added Work.");
    expect(await screen.findByRole("region", { name: "Work" })).toBeTruthy();
    expect(screen.queryByRole("region", { name: "New category" })).toBeNull();
  });

  it("shows why the backend refused a category", async () => {
    const user = userEvent.setup();
    apiClient.addMemoryCategory.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/memory-categories",
        "There is already a category called Goals.",
      ),
    );
    renderWithQueries(<MemoryCategoriesManager />);
    await findCard("Goals");

    await user.click(screen.getByRole("button", { name: "Add category" }));
    const box = await findCard("New category");
    await user.type(box.getByLabelText("Name"), "goals");
    await user.type(box.getByLabelText("Description"), "Again");
    await user.click(box.getByRole("button", { name: "Add" }));

    expect(await box.findByRole("alert")).toHaveTextContent(
      "There is already a category called Goals.",
    );
  });

  it("renames a category and edits its description", async () => {
    const user = userEvent.setup();
    apiClient.updateMemoryCategory.mockResolvedValue({
      ...goals,
      name: "Aims",
    });
    renderWithQueries(<MemoryCategoriesManager />);
    const card = await findCard("Goals");

    const name = card.getByLabelText("Name");
    expect(name).toHaveValue("Goals");
    await user.clear(name);
    await user.type(name, "Aims");
    const description = card.getByLabelText("Description");
    await user.clear(description);
    await user.type(description, "What they work towards");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateMemoryCategory).toHaveBeenCalledWith("goals", {
      name: "Aims",
      description: "What they work towards",
      always_include: false,
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Saved Aims.");
  });

  it("turns always include on and off as soon as it is switched", async () => {
    const user = userEvent.setup();
    apiClient.updateMemoryCategory.mockResolvedValue({
      ...goals,
      always_include: true,
    });
    renderWithQueries(<MemoryCategoriesManager />);
    const card = await findCard("Goals");

    await user.click(
      card.getByRole("switch", { name: "Always include Goals" }),
    );

    expect(apiClient.updateMemoryCategory).toHaveBeenCalledWith("goals", {
      name: "Goals",
      description: "About Goals",
      always_include: true,
    });
    await vi.waitFor(() =>
      expect(apiClient.listMemoryCategories).toHaveBeenCalledTimes(2),
    );
  });

  it("archives an active category after confirming and restores an archived one", async () => {
    const user = userEvent.setup();
    apiClient.archiveMemoryCategory.mockResolvedValue({
      ...goals,
      archived: true,
    });
    apiClient.restoreMemoryCategory.mockResolvedValue({
      ...habits,
      archived: false,
    });
    renderWithQueries(<MemoryCategoriesManager />);
    const goalsCard = await findCard("Goals");

    await user.click(goalsCard.getByRole("button", { name: "Archive" }));
    expect(apiClient.archiveMemoryCategory).not.toHaveBeenCalled();
    const confirm = goalsCard.getByRole("alertdialog", {
      name: "Archive this category?",
    });
    await user.click(within(confirm).getByRole("button", { name: "Archive" }));
    expect(apiClient.archiveMemoryCategory).toHaveBeenCalledWith("goals");
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Archived Goals. Its memories are kept.",
    );

    const habitsCard = await findCard("Habits (old)");
    await user.click(habitsCard.getByRole("button", { name: "Restore" }));
    expect(apiClient.restoreMemoryCategory).toHaveBeenCalledWith("habits");
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Restored Habits (old).",
    );
  });

  async function archiveGoals(user: ReturnType<typeof userEvent.setup>) {
    const card = await findCard("Goals");
    await user.click(card.getByRole("button", { name: "Archive" }));
    await user.click(
      within(card.getByRole("alertdialog")).getByRole("button", {
        name: "Archive",
      }),
    );
  }

  it("says when a change fails", async () => {
    const user = userEvent.setup();
    apiClient.archiveMemoryCategory.mockRejectedValue(new Error("offline"));
    renderWithQueries(<MemoryCategoriesManager />);

    await archiveGoals(user);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t change Goals. Please try again.",
    );
  });

  it("shows why a Required Memory Category can't be archived", async () => {
    const user = userEvent.setup();
    const reason =
      "Goals is a Required Memory Category (used by onboarding and the Home page), so it can't be archived.";
    apiClient.archiveMemoryCategory.mockRejectedValue(
      new ApiError(409, "/api/admin/memory-categories/goals/archive", reason),
    );
    renderWithQueries(<MemoryCategoriesManager />);

    await archiveGoals(user);

    expect(await screen.findByRole("alert")).toHaveTextContent(reason);
  });

  it("shows the empty state when there are no categories", async () => {
    apiClient.listMemoryCategories.mockResolvedValue([]);

    renderWithQueries(<MemoryCategoriesManager />);

    expect(await screen.findByText("No categories yet")).toBeInTheDocument();
  });

  it("offers to try again when the categories can't be loaded", async () => {
    const user = userEvent.setup();
    apiClient.listMemoryCategories.mockRejectedValueOnce(new Error("offline"));
    renderWithQueries(<MemoryCategoriesManager />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn’t load Memory Categories");
    await user.click(within(alert).getByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("region", { name: "Goals" }),
    ).toBeInTheDocument();
  });
});
