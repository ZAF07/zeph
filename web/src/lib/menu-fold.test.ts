import { describe, expect, it, vi } from "vitest";

import {
  isMenuFoldedCookie,
  MENU_FOLDED_COOKIE,
  readMenuFolded,
  saveMenuFolded,
  saveMenuFoldedCookie,
} from "@/lib/menu-fold";

/**
 * Builds a working in-memory storage for a test.
 *
 * @returns A storage that keeps what is saved to it.
 */
function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key) => values.get(key) ?? null,
    key: (index) => [...values.keys()][index] ?? null,
    removeItem: (key) => values.delete(key),
    setItem: (key, value) => values.set(key, value),
  };
}

/**
 * Stands in for a browser that blocks site storage: even reaching it throws.
 *
 * @returns Never; it always throws.
 */
function blockedStorage(): Storage {
  throw new DOMException("Storage is blocked", "SecurityError");
}

describe("menu fold", () => {
  it("reads nothing when nothing has been saved", () => {
    const storage = memoryStorage();

    expect(readMenuFolded(() => storage)).toBeNull();
  });

  it("reads back the fold that was saved", () => {
    const storage = memoryStorage();

    saveMenuFolded(() => storage, true);
    expect(readMenuFolded(() => storage)).toBe(true);

    saveMenuFolded(() => storage, false);
    expect(readMenuFolded(() => storage)).toBe(false);
  });

  it("reads nothing, and saves nothing, when storage is blocked", () => {
    expect(readMenuFolded(blockedStorage)).toBeNull();
    expect(() => saveMenuFolded(blockedStorage, true)).not.toThrow();
  });

  it("saves the fold in a cookie the server can read for a year", () => {
    const writeCookie = vi.fn();

    saveMenuFoldedCookie(writeCookie, true);

    expect(writeCookie).toHaveBeenCalledWith(
      `${MENU_FOLDED_COOKIE}=1; path=/; max-age=31536000; samesite=lax`,
    );
  });

  it("saves nothing, without failing, when cookies are blocked", () => {
    const blockedCookies = () => {
      throw new DOMException("Cookies are blocked", "SecurityError");
    };

    expect(() => saveMenuFoldedCookie(blockedCookies, true)).not.toThrow();
  });

  it("reads the cookie as folded only when it says so", () => {
    expect(isMenuFoldedCookie("1")).toBe(true);
    expect(isMenuFoldedCookie("0")).toBe(false);
    expect(isMenuFoldedCookie(undefined)).toBe(false);
  });
});
