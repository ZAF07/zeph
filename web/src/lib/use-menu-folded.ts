"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { hasDesignFlag } from "@/lib/design-flags";
import {
  readMenuFolded,
  saveMenuFolded,
  saveMenuFoldedCookie,
} from "@/lib/menu-fold";

/**
 * Returns the browser's `localStorage`. Reaching it throws when the browser
 * blocks storage, which `menu-fold` guards against.
 *
 * @returns The browser's `localStorage`.
 */
function browserStorage(): Storage {
  return window.localStorage;
}

/**
 * Sets one cookie in the browser.
 *
 * @param cookie - The cookie's `name=value; …` line.
 */
function writeBrowserCookie(cookie: string): void {
  document.cookie = cookie;
}

/**
 * Whether the sidebar is folded into the icon rail. It starts from the fold
 * cookie the server read, then follows `localStorage` when that has a saved
 * choice. Folding saves to both. `?design=menu-folded` forces the rail in
 * design-fixture mode.
 *
 * @param initialMenuFolded - Whether the fold cookie said the sidebar is folded.
 * @param getStorage - Returns the storage the fold is kept in.
 * @param writeCookie - Sets the fold cookie.
 * @returns Whether the sidebar is folded, and a function to fold or unfold it.
 */
export function useMenuFolded(
  initialMenuFolded: boolean,
  getStorage: () => Storage = browserStorage,
  writeCookie: (cookie: string) => void = writeBrowserCookie,
): [boolean, (folded: boolean) => void] {
  const forcedFolded = hasDesignFlag(useSearchParams(), "menu-folded");
  const [menuFolded, setMenuFolded] = useState(
    forcedFolded || initialMenuFolded,
  );

  useEffect(() => {
    const savedFolded = readMenuFolded(getStorage);
    if (!forcedFolded && savedFolded !== null) {
      setMenuFolded(savedFolded);
    }
  }, [forcedFolded, getStorage]);

  function changeMenuFolded(folded: boolean): void {
    setMenuFolded(folded);
    saveMenuFolded(getStorage, folded);
    saveMenuFoldedCookie(writeCookie, folded);
  }

  return [menuFolded, changeMenuFolded];
}
