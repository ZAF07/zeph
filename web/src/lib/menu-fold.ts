/** Where the browser keeps whether the sidebar is folded into the rail. */
const MENU_FOLDED_KEY = "zeph-menu-folded";

/**
 * Reads whether the User folded the sidebar last time. A browser that blocks
 * storage throws even when storage is reached, so both steps are guarded.
 *
 * @param getStorage - Returns the storage to read, such as `localStorage`.
 * @returns True when the sidebar was folded; false when not, or unknown.
 */
export function readMenuFolded(getStorage: () => Storage): boolean {
  try {
    return getStorage().getItem(MENU_FOLDED_KEY) === "1";
  } catch {
    return false;
  }
}

/**
 * Saves whether the sidebar is folded. When storage is blocked, nothing is
 * saved and the fold lasts only until the page reloads.
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
