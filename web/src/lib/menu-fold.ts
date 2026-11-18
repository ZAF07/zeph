/** Where the browser keeps whether the sidebar is folded into the rail. */
const MENU_FOLDED_KEY = "zeph-menu-folded";

/**
 * The cookie that tells the server the sidebar is folded, so the first
 * paint already shows the rail instead of jumping to it.
 */
export const MENU_FOLDED_COOKIE = "zeph-menu-folded";

/** How long the fold cookie lasts: a year, in seconds. */
const MENU_FOLDED_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

/**
 * Reads whether the User folded the sidebar last time. A browser that blocks
 * storage throws even when storage is reached, so both steps are guarded.
 *
 * @param getStorage - Returns the storage to read, such as `localStorage`.
 * @returns True or false as saved; null when nothing is saved or storage is blocked.
 */
export function readMenuFolded(getStorage: () => Storage): boolean | null {
  try {
    const saved = getStorage().getItem(MENU_FOLDED_KEY);
    return saved === null ? null : saved === "1";
  } catch {
    return null;
  }
}

/**
 * Saves whether the sidebar is folded. When storage is blocked, nothing is
 * saved.
 *
 * @param getStorage - Returns the storage to write, such as `localStorage`.
 * @param folded - Whether the sidebar is folded.
 */
export function saveMenuFolded(
  getStorage: () => Storage,
  folded: boolean,
): void {
  try {
    getStorage().setItem(MENU_FOLDED_KEY, folded ? "1" : "0");
  } catch {}
}

/**
 * Saves whether the sidebar is folded in the cookie the server reads. When
 * cookies are blocked, nothing is saved.
 *
 * @param writeCookie - Sets one cookie from its `name=value; …` line.
 * @param folded - Whether the sidebar is folded.
 */
export function saveMenuFoldedCookie(
  writeCookie: (cookie: string) => void,
  folded: boolean,
): void {
  try {
    writeCookie(
      `${MENU_FOLDED_COOKIE}=${folded ? "1" : "0"}; path=/; max-age=${MENU_FOLDED_COOKIE_MAX_AGE}; samesite=lax`,
    );
  } catch {}
}

/**
 * Reads the fold cookie's value.
 *
 * @param value - The cookie's value, or undefined when it isn't set.
 * @returns True when the cookie says the sidebar is folded.
 */
export function isMenuFoldedCookie(value: string | undefined): boolean {
  return value === "1";
}
