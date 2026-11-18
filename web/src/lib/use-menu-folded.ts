"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { hasDesignFlag } from "@/lib/design-flags";
import { readMenuFolded, saveMenuFolded } from "@/lib/menu-fold";

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
 * Whether the sidebar is folded into the icon rail, remembered in the
 * browser. `?design=menu-folded` forces the rail in design-fixture mode.
 *
 * @param getStorage - Returns the storage the fold is kept in.
 * @returns Whether the sidebar is folded, and a function to fold or unfold it.
 */
export function useMenuFolded(
  getStorage: () => Storage = browserStorage,
): [boolean, (folded: boolean) => void] {
  const forcedFolded = hasDesignFlag(useSearchParams(), "menu-folded");
  const [menuFolded, setMenuFolded] = useState(forcedFolded);

  useEffect(() => {
    if (!forcedFolded) {
      setMenuFolded(readMenuFolded(getStorage));
    }
  }, [forcedFolded, getStorage]);

  function changeMenuFolded(folded: boolean): void {
    setMenuFolded(folded);
    saveMenuFolded(getStorage, folded);
  }

  return [menuFolded, changeMenuFolded];
}
