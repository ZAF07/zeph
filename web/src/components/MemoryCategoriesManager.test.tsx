import { screen, within } from "@testing-library/react";
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

function section(name: RegExp): ReturnType<typeof within> {
  return within(screen.getByRole("region", { name }));
}

function rowFor(name: string): ReturnType<typeof within> {
  const row = screen.getByText(name).closest("li");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return within(row);
}

describe("MemoryCategoriesManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listMemoryCategories.mockResolvedValue([goals, values, habits]);
  });

  it("lists active and archived categories with their item counts", async () => {
    renderWithQueries(<MemoryCategoriesManager />);

    await screen.findByText("Goals");
    const active = section(/Active/);
    expect(active.getByText("Goals")).toBeInTheDocument();
    expect(active.getByText("· 97 items")).toBeInTheDocument();
    expect(active.getByText("About Goals")).toBeInTheDocument();
    expect(active.getByText("Values & beliefs")).toBeInTheDocument();
    expect(active.queryByText("Habits (old)")).toBeNull();
    expect(
      active.getByRole("switch", { name: "Always include Values & beliefs" }),
    ).toHaveAttribute("aria-checked", "true");
    expect(
      active.getByRole("switch", { name: "Always include Goals" }),
    ).toHaveAttribute("aria-checked", "false");
    const archived = section(/Archived/);
    expect(archived.getByText("Habits (old)")).toBeInTheDocument();
    expect(archived.getByText("· 23 items kept")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Delete/ })).toBeNull();
  });

  it("says when nothing is archived", async () => {
    apiClient.listMemoryCategories.mockResolvedValue([goals]);

    renderWithQueries(<MemoryCategoriesManager />);

    expect(await screen.findByText("Nothing archived.")).toBeInTheDocument();
  });

  it("adds a category and shows it in the list", async () => {
    const user = userEvent.setup();
    const work = category("work", "Work", {
      description: "Job and colleagues",
      item_count: 0,
    });
    apiClient.addMemoryCategory.mockResolvedValue(work);
    renderWithQueries(<MemoryCategoriesManager />);
    await screen.findByText("Goals");
    apiClient.listMemoryCategories.mockResolvedValue([goals, values, work]);

    await user.click(screen.getByRole("button", { name: "Add category" }));
    const form = within(screen.getByRole("form", { name: "New category" }));
    await user.type(form.getByLabelText("Name"), "Work");
    await user.type(form.getByLabelText(/Description/), "Job and colleagues");
    await user.click(form.getByRole("button", { name: "Save category" }));

    expect(apiClient.addMemoryCategory).toHaveBeenCalledWith({
      name: "Work",
      description: "Job and colleagues",
      always_include: false,
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Added Work.");
    expect(section(/Active/).getByText("Work")).toBeInTheDocument();
    expect(screen.queryByRole("form", { name: "New category" })).toBeNull();
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
    await screen.findByText("Goals");

    await user.click(screen.getByRole("button", { name: "Add category" }));
    const form = within(screen.getByRole("form", { name: "New category" }));
    await user.type(form.getByLabelText("Name"), "goals");
    await user.type(form.getByLabelText(/Description/), "Again");
    await user.click(form.getByRole("button", { name: "Save category" }));

    expect(await form.findByRole("alert")).toHaveTextContent(
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
    await screen.findByText("Goals");

    await user.click(rowFor("Goals").getByRole("button", { name: "Edit" }));
    const form = within(screen.getByRole("form", { name: "Edit Goals" }));
    const name = form.getByLabelText("Name");
    expect(name).toHaveValue("Goals");
    await user.clear(name);
    await user.type(name, "Aims");
    const description = form.getByLabelText(/Description/);
    await user.clear(description);
    await user.type(description, "What they work towards");
    await user.click(form.getByRole("button", { name: "Save category" }));

    expect(apiClient.updateMemoryCategory).toHaveBeenCalledWith("goals", {
      name: "Aims",
      description: "What they work towards",
      always_include: false,
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Saved Aims.");
  });

  it("turns always include on and off", async () => {
    const user = userEvent.setup();
    apiClient.updateMemoryCategory.mockResolvedValue({
      ...goals,
      always_include: true,
    });
    renderWithQueries(<MemoryCategoriesManager />);
    await screen.findByText("Goals");

    await user.click(
      screen.getByRole("switch", { name: "Always include Goals" }),
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

  it("archives an active category and restores an archived one", async () => {
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
    await screen.findByText("Goals");

    await user.click(rowFor("Goals").getByRole("button", { name: "Archive" }));
    expect(apiClient.archiveMemoryCategory).toHaveBeenCalledWith("goals");
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Archived Goals. Its memories are kept.",
    );

    await user.click(
      rowFor("Habits (old)").getByRole("button", { name: "Restore" }),
    );
    expect(apiClient.restoreMemoryCategory).toHaveBeenCalledWith("habits");
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Restored Habits (old).",
    );
  });

  it("says when a change fails", async () => {
    const user = userEvent.setup();
    apiClient.archiveMemoryCategory.mockRejectedValue(new Error("offline"));
    renderWithQueries(<MemoryCategoriesManager />);
    await screen.findByText("Goals");

    await user.click(rowFor("Goals").getByRole("button", { name: "Archive" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
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
    await screen.findByText("Goals");

    await user.click(rowFor("Goals").getByRole("button", { name: "Archive" }));

    expect(await screen.findByRole("status")).toHaveTextContent(reason);
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

    expect(await screen.findByText("Goals")).toBeInTheDocument();
  });
});
