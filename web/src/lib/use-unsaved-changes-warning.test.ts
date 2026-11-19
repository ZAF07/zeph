import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useUnsavedChangesWarning } from "@/lib/use-unsaved-changes-warning";

const router = { push: vi.fn() };

vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

function addLink(href: string, attributes: Record<string, string> = {}) {
  const link = document.createElement("a");
  link.href = href;
  link.textContent = "Go";
  for (const [name, value] of Object.entries(attributes)) {
    link.setAttribute(name, value);
  }
  document.body.append(link);
  return link;
}

function click(link: HTMLElement, options: MouseEventInit = {}) {
  const event = new MouseEvent("click", {
    bubbles: true,
    cancelable: true,
    button: 0,
    ...options,
  });
  act(() => {
    link.dispatchEvent(event);
  });
  return event;
}

describe("useUnsavedChangesWarning", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    vi.resetAllMocks();
  });

  it("holds a plain in-app link until the person leaves", () => {
    const { result } = renderHook(() => useUnsavedChangesWarning(true));
    const event = click(addLink("/admin/knowledge?tab=all"));

    expect(event.defaultPrevented).toBe(true);
    expect(result.current.leavingTo).toBe("/admin/knowledge?tab=all");

    act(() => result.current.leave());
    expect(router.push).toHaveBeenCalledWith("/admin/knowledge?tab=all");
    expect(result.current.leavingTo).toBeNull();
  });

  it("drops the held link when the person stays", () => {
    const { result } = renderHook(() => useUnsavedChangesWarning(true));
    click(addLink("/admin/knowledge"));

    act(() => result.current.stay());

    expect(result.current.leavingTo).toBeNull();
    expect(router.push).not.toHaveBeenCalled();
  });

  it("leaves new-tab, download, off-site and same-page links to the browser", () => {
    const { result } = renderHook(() => useUnsavedChangesWarning(true));
    const passed = [
      click(addLink("/admin/knowledge"), { metaKey: true }),
      click(addLink("/admin/knowledge"), { button: 1 }),
      click(addLink("/admin/knowledge", { target: "_blank" })),
      click(addLink("/files/doc.pdf", { download: "" })),
      click(addLink("https://example.com/elsewhere")),
      click(addLink("#text")),
    ];

    expect(passed.every((event) => !event.defaultPrevented)).toBe(true);
    expect(result.current.leavingTo).toBeNull();
  });

  it("holds nothing without unsaved changes", () => {
    const { result } = renderHook(() => useUnsavedChangesWarning(false));
    const event = click(addLink("/admin/knowledge"));

    expect(event.defaultPrevented).toBe(false);
    expect(result.current.leavingTo).toBeNull();
  });
});
