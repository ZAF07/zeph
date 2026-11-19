import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CopyEditor } from "@/components/CopyEditor";
import { ApiError, type ApiClient, type CopyTab } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getCopyPage: vi.fn<ApiClient["getCopyPage"]>(),
  saveCopyTab: vi.fn<ApiClient["saveCopyTab"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const router = { push: vi.fn() };

vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

const copyPage: CopyTab[] = [
  {
    tab: "landing",
    name: "Landing",
    slots: [
      {
        key: "landing.hero.eyebrow",
        name: "Label above the main heading",
        text: "Your AI companion",
        max_length: 40,
        placeholders: [],
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: null,
      },
      {
        key: "landing.hero.heading_first_line",
        name: "Main heading, first line",
        text: "Think Deeper,",
        max_length: 20,
        placeholders: [],
        updated_at: "2026-11-08T14:20:00Z",
        updated_by: "Maya Lin",
      },
      {
        key: "landing.memory_count",
        name: "Memory count",
        text: "{count} Memory Items",
        max_length: 40,
        placeholders: ["count"],
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: null,
      },
    ],
  },
  {
    tab: "pricing",
    name: "Pricing",
    slots: [
      {
        key: "pricing.plus.button",
        name: "Plus plan: button",
        text: "Start Plus",
        max_length: 20,
        placeholders: [],
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: null,
      },
    ],
  },
];

describe("CopyEditor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getCopyPage.mockResolvedValue(copyPage);
    apiClient.saveCopyTab.mockImplementation(async (_tab, texts) =>
      copyPage.map((tab) => ({
        ...tab,
        slots: tab.slots.map((slot) =>
          slot.key in texts
            ? {
                ...slot,
                text: texts[slot.key],
                updated_at: "2026-11-11T10:00:00Z",
                updated_by: "Maya Lin",
              }
            : slot,
        ),
      })),
    );
  });

  it("shows the Landing tab's slots in page order, each with its details", async () => {
    renderWithQueries(<CopyEditor />);

    expect(
      await screen.findByRole("tab", { name: "Landing", selected: true }),
    ).toBeVisible();
    const editors = screen.getAllByRole("textbox");
    expect(editors.map((editor) => editor.getAttribute("aria-label"))).toEqual([
      "Label above the main heading",
      "Main heading, first line",
      "Memory count",
    ]);
    expect(
      screen.getByRole("textbox", { name: "Main heading, first line" }),
    ).toHaveValue("Think Deeper,");
    expect(screen.getByText("13 / 20 characters")).toBeVisible();
    expect(screen.getByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(screen.getAllByText("Seed text")).toHaveLength(2);
    expect(screen.getByText("Takes {count}")).toBeVisible();
  });

  it("saves every changed slot in the tab as one save", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CopyEditor />);
    const heading = await screen.findByRole("textbox", {
      name: "Main heading, first line",
    });

    await user.clear(heading);
    await user.type(heading, "Think Slower,");
    await user.type(
      screen.getByRole("textbox", { name: "Label above the main heading" }),
      "!",
    );
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(apiClient.saveCopyTab).toHaveBeenCalledTimes(1);
    expect(apiClient.saveCopyTab).toHaveBeenCalledWith("landing", {
      "landing.hero.heading_first_line": "Think Slower,",
      "landing.hero.eyebrow": "Your AI companion!",
    });
    expect(
      await screen.findByText("Saved. It shows on the next page load."),
    ).toBeVisible();
    expect(
      screen.getByRole("textbox", { name: "Main heading, first line" }),
    ).toHaveValue("Think Slower,");
  });

  it("shows each reason a save was turned away on its own slot", async () => {
    apiClient.saveCopyTab.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/copy/landing",
        "Some texts can’t be saved. See each one.",
        {
          "landing.hero.heading_first_line":
            "Keep it to 20 characters or fewer.",
          "landing.memory_count": "Keep {count} in the text.",
        },
      ),
    );
    const user = userEvent.setup();
    renderWithQueries(<CopyEditor />);

    await user.type(
      await screen.findByRole("textbox", { name: "Main heading, first line" }),
      " and much more",
    );
    await user.clear(screen.getByRole("textbox", { name: "Memory count" }));
    await user.type(
      screen.getByRole("textbox", { name: "Memory count" }),
      "Memory Items",
    );
    await user.click(screen.getByRole("button", { name: "Save" }));

    const heading = screen.getByRole("group", {
      name: "Main heading, first line",
    });
    expect(
      await within(heading).findByText("Keep it to 20 characters or fewer."),
    ).toBeVisible();
    expect(
      within(screen.getByRole("group", { name: "Memory count" })).getByText(
        "Keep {count} in the text.",
      ),
    ).toBeVisible();
    expect(
      within(
        screen.getByRole("group", { name: "Label above the main heading" }),
      ).queryByRole("alert"),
    ).toBeNull();
    expect(
      screen.getByText("Some texts can’t be saved. See each one."),
    ).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Memory count" })).toHaveValue(
      "Memory Items",
    );
  });

  it("discards unsaved edits", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CopyEditor />);
    const heading = await screen.findByRole("textbox", {
      name: "Main heading, first line",
    });

    await user.type(heading, " Now");
    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(heading).toHaveValue("Think Deeper,");
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("asks before switching tabs with unsaved edits, and keeps them on Keep editing", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CopyEditor />);
    const heading = await screen.findByRole("textbox", {
      name: "Main heading, first line",
    });
    await user.type(heading, " Now");

    await user.click(screen.getByRole("tab", { name: "Pricing" }));
    const dialog = screen.getByRole("alertdialog", {
      name: "Switch tabs and lose your changes?",
    });
    await user.click(
      within(dialog).getByRole("button", { name: "Keep editing" }),
    );

    expect(screen.getByRole("tab", { name: "Landing" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(heading).toHaveValue("Think Deeper, Now");
    expect(screen.queryByRole("alertdialog")).toBeNull();
  });

  it("switches tabs and drops the edits once the Admin says to", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CopyEditor />);
    await user.type(
      await screen.findByRole("textbox", { name: "Main heading, first line" }),
      " Now",
    );

    await user.click(screen.getByRole("tab", { name: "Pricing" }));
    await user.click(screen.getByRole("button", { name: "Switch tab" }));

    expect(
      screen.getByRole("textbox", { name: "Plus plan: button" }),
    ).toHaveValue("Start Plus");
    await user.click(screen.getByRole("tab", { name: "Landing" }));
    expect(
      screen.getByRole("textbox", { name: "Main heading, first line" }),
    ).toHaveValue("Think Deeper,");
  });

  it("switches tabs without asking when nothing is unsaved", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CopyEditor />);
    await user.type(
      await screen.findByRole("textbox", { name: "Main heading, first line" }),
      " Now",
    );
    await user.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Saved. It shows on the next page load.");

    await user.click(screen.getByRole("tab", { name: "Pricing" }));

    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(
      screen.getByRole("textbox", { name: "Plus plan: button" }),
    ).toBeVisible();
  });

  it("asks before following a link away with unsaved edits", async () => {
    const user = userEvent.setup();
    renderWithQueries(
      <>
        <a href="/admin/settings">Platform settings</a>
        <CopyEditor />
      </>,
    );
    await user.type(
      await screen.findByRole("textbox", { name: "Main heading, first line" }),
      " Now",
    );

    await user.click(screen.getByRole("link", { name: "Platform settings" }));
    await user.click(
      within(
        screen.getByRole("alertdialog", {
          name: "Leave and lose your changes?",
        }),
      ).getByRole("button", { name: "Leave" }),
    );

    expect(router.push).toHaveBeenCalledWith("/admin/settings");
  });

  it("says when the Copy page couldn't load", async () => {
    apiClient.getCopyPage.mockRejectedValue(new Error("offline"));
    renderWithQueries(<CopyEditor />);

    expect(await screen.findByText("Couldn’t load Copy")).toBeVisible();
    expect(screen.getByRole("button", { name: "Try again" })).toBeVisible();
  });
});
