import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardShell } from "@/components/DashboardShell";
import type { ApiClient } from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const signOut = vi.hoisted(() => vi.fn());

vi.mock("@/lib/auth/client", () => ({
  useSignOut: () => signOut,
}));

const designMode = vi.hoisted(() => ({ on: false }));

vi.mock("@/env", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/env")>();
  return {
    ...actual,
    env: {
      ...actual.env,
      get designFixtures() {
        return designMode.on;
      },
    },
  };
});

const navigation = vi.hoisted(() => ({ pathname: "/", search: "" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useSearchParams: () => new URLSearchParams(navigation.search),
}));

/**
 * Renders the shell around a stand-in page.
 *
 * @param initialMenuFolded - Whether the fold cookie says the sidebar is folded.
 * @returns What Testing Library's `render` returns.
 */
function renderShell(initialMenuFolded = false) {
  return renderWithQueries(
    <DashboardShell initialMenuFolded={initialMenuFolded}>
      <p>Page content</p>
    </DashboardShell>,
  );
}

/**
 * Finds the phone menu panel, which only exists while the menu is open.
 *
 * @returns The panel, or null when the menu is closed.
 */
function phoneMenu(): HTMLElement | null {
  return document.getElementById("phone-menu");
}

describe("DashboardShell", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.localStorage.clear();
    navigation.pathname = "/";
    navigation.search = "";
    designMode.on = false;
    apiClient.getMe.mockResolvedValue(userWithRole("user"));
    apiClient.getPlatformContent.mockResolvedValue({
      ai_notice: "Long notice.",
      ai_notice_short: "Zeph is an AI, not a therapist or crisis service.",
      user_memory_explanation: "",
      photo_viewing_explanation: "",
      onboarding_reason_choices: [],
      message_retention_days: 30,
      delete_my_data_description: "",
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the page beside the sidebar's menu, AI notice and person", async () => {
    renderShell();

    const sidebar = screen.getByRole("complementary");
    expect(screen.getByRole("main")).toHaveTextContent("Page content");
    const links = within(sidebar).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "Zeph",
      "Home",
      "Memories",
      "Check-ins",
      "Account & privacy",
      "PlanTo build",
    ]);
    expect(within(sidebar).getByRole("link", { name: "Home" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(
      await within(sidebar).findByText(
        "Zeph is an AI, not a therapist or crisis service.",
      ),
    ).toBeInTheDocument();
    expect(await within(sidebar).findByText("Maya")).toBeInTheDocument();
    expect(within(sidebar).getByText("maya@example.com")).toBeInTheDocument();
  });

  it("signs out from the sidebar", async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(
      within(screen.getByRole("complementary")).getByRole("button", {
        name: "Sign out",
      }),
    );

    expect(signOut).toHaveBeenCalledWith("/sign-in");
  });

  it("folds the sidebar into the icon rail, and remembers it after a reload", async () => {
    const user = userEvent.setup();
    const firstVisit = renderShell();

    await user.click(screen.getByRole("button", { name: "Fold the menu" }));

    const rail = screen.getByRole("complementary");
    expect(
      within(rail).getByRole("button", { name: "Unfold the menu" }),
    ).toBeInTheDocument();
    expect(
      within(rail).getByRole("link", { name: "Memories" }),
    ).toHaveAttribute("title", "Memories");
    expect(within(rail).queryByText("Memories")).toBeNull();

    firstVisit.unmount();
    renderShell();

    expect(
      await screen.findByRole("button", { name: "Unfold the menu" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Unfold the menu" }));
    expect(
      screen.getByRole("button", { name: "Fold the menu" }),
    ).toBeInTheDocument();
  });

  it("draws the rail from the first paint when the fold cookie says so", () => {
    renderShell(true);

    expect(
      screen.getByRole("button", { name: "Unfold the menu" }),
    ).toBeInTheDocument();
  });

  it("saves the fold in a cookie, so the server draws it next time", async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole("button", { name: "Fold the menu" }));
    expect(document.cookie).toContain("zeph-menu-folded=1");

    await user.click(screen.getByRole("button", { name: "Unfold the menu" }));
    expect(document.cookie).toContain("zeph-menu-folded=0");
  });

  it("keeps the cookie's fold when the browser blocks storage", () => {
    vi.spyOn(window, "localStorage", "get").mockImplementation(() => {
      throw new DOMException("Storage is blocked", "SecurityError");
    });

    renderShell(true);

    expect(
      screen.getByRole("button", { name: "Unfold the menu" }),
    ).toBeInTheDocument();
  });

  it("still folds and unfolds when the browser blocks storage", async () => {
    vi.spyOn(window, "localStorage", "get").mockImplementation(() => {
      throw new DOMException("Storage is blocked", "SecurityError");
    });
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole("button", { name: "Fold the menu" }));
    expect(
      screen.getByRole("button", { name: "Unfold the menu" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Unfold the menu" }));
    expect(
      screen.getByRole("button", { name: "Fold the menu" }),
    ).toBeInTheDocument();
  });

  it("shows the rail when the address asks for it in design-fixture mode", () => {
    designMode.on = true;
    navigation.search = "design=menu-folded";

    renderShell();

    expect(
      screen.getByRole("button", { name: "Unfold the menu" }),
    ).toBeInTheDocument();
  });

  it("opens the phone menu when the address asks for it in design-fixture mode", () => {
    designMode.on = true;
    navigation.search = "design=menu-open";

    renderShell();

    expect(phoneMenu()).not.toBeNull();
  });

  it("ignores ?design= outside design-fixture mode", () => {
    navigation.search = "design=menu-folded";

    renderShell();

    expect(
      screen.getByRole("button", { name: "Fold the menu" }),
    ).toBeInTheDocument();
  });

  it("opens the phone menu with a cross, and closes it when a link is chosen", async () => {
    const user = userEvent.setup();
    renderShell();

    expect(phoneMenu()).toBeNull();
    const menuButton = screen.getByRole("button", { name: "Open the menu" });
    expect(menuButton).toHaveAttribute("aria-expanded", "false");

    await user.click(menuButton);

    const closeButton = screen.getByRole("button", { name: "Close the menu" });
    expect(closeButton).toHaveAttribute("aria-expanded", "true");
    const menu = phoneMenu();
    expect(menu).not.toBeNull();
    expect(
      await within(menu as HTMLElement).findByText("Maya"),
    ).toBeInTheDocument();

    await user.click(
      within(menu as HTMLElement).getByRole("link", { name: "Memories" }),
    );

    expect(phoneMenu()).toBeNull();
    expect(
      screen.getByRole("button", { name: "Open the menu" }),
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("closes the phone menu with the cross", async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole("button", { name: "Open the menu" }));
    await user.click(screen.getByRole("button", { name: "Close the menu" }));

    expect(phoneMenu()).toBeNull();
  });

  it("closes the phone menu when the wordmark is chosen", async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole("button", { name: "Open the menu" }));
    await user.click(
      within(screen.getByRole("banner")).getByRole("link", { name: "Zeph" }),
    );

    expect(phoneMenu()).toBeNull();
  });

  it("closes the phone menu when the page changes, as with Back", async () => {
    const user = userEvent.setup();
    const shell = renderShell();

    await user.click(screen.getByRole("button", { name: "Open the menu" }));
    navigation.pathname = "/memories";
    shell.rerender(
      <DashboardShell initialMenuFolded={false}>
        <p>Page content</p>
      </DashboardShell>,
    );

    expect(phoneMenu()).toBeNull();
  });

  it("shows the Admin section to an Admin, with Admin in place of the email", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));
    navigation.pathname = "/admin/persona";
    const user = userEvent.setup();
    renderShell();

    const sidebar = screen.getByRole("complementary");
    const adminGroup = await within(sidebar).findByRole("group", {
      name: "Admin",
    });
    expect(
      within(adminGroup)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual([
      "OverviewTo build",
      "Users",
      "Persona",
      "Prompts & models",
      "Safety",
      "Safeguard Events",
      "Knowledge",
      "Memory Categories",
      "Needs",
      "Moves",
      "Check-in Kinds",
      "Check-in log",
      "Check-in Schedule",
      "Sticker Library",
      "Features",
      "Platform settings",
      "Usage",
      "Model call log",
      "Evals",
      "PlansTo build",
    ]);
    expect(
      within(adminGroup).getByRole("link", { name: "Persona" }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(adminGroup).getByRole("link", { name: "Overview To build" }),
    ).not.toHaveAttribute("aria-current");
    expect(within(sidebar).queryByText("maya@example.com")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Open the menu" }));
    expect(
      within(phoneMenu() as HTMLElement).getByRole("group", { name: "Admin" }),
    ).toBeInTheDocument();
  });

  it("keeps an admin link marked on the pages under it", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));
    navigation.pathname = "/admin/knowledge/letters";
    renderShell();

    const adminGroup = await screen.findByRole("group", { name: "Admin" });
    expect(
      within(adminGroup).getByRole("link", { name: "Knowledge" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("hides the Admin section from a User", async () => {
    renderShell();

    await screen.findByText("Maya");
    expect(screen.queryByRole("group", { name: "Admin" })).toBeNull();
  });
});
