import { describe, expect, it } from "vitest";

import { readMenuFolded, saveMenuFolded } from "@/lib/menu-fold";

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
  it("reads as unfolded when nothing has been saved", () => {
    const storage = memoryStorage();

    expect(readMenuFolded(() => storage)).toBe(false);
  });

  it("reads back the fold that was saved", () => {
    const storage = memoryStorage();

    saveMenuFolded(() => storage, true);
    expect(readMenuFolded(() => storage)).toBe(true);

    saveMenuFolded(() => storage, false);
    expect(readMenuFolded(() => storage)).toBe(false);
  });

  it("reads as unfolded, and saves nothing, when storage is blocked", () => {
    expect(readMenuFolded(blockedStorage)).toBe(false);
    expect(() => saveMenuFolded(blockedStorage, true)).not.toThrow();
  });
});
