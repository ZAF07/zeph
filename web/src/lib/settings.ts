import type { AdminSettings } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";

/**
 * Reads a setting's value as text.
 *
 * @param settings - The settings, by key.
 * @param key - The setting to read.
 * @returns Its value as text, or "" if it is missing.
 */
export function textSetting(settings: AdminSettings, key: string): string {
  const setting = settings[key];
  return setting ? String(setting.value) : "";
}

/**
 * Says when some settings were last saved by an Admin, and by whom.
 *
 * @param settings - The settings, by key.
 * @param keys - The settings to look at.
 * @param timeZone - The time zone to show the time in; the browser's by
 *   default.
 * @returns A note like "Last saved 8 Nov, 14:20 by Maya Lin".
 */
export function lastSavedNote(
  settings: AdminSettings,
  keys: string[],
  timeZone?: string,
): string {
  const savedByAdmins = keys
    .map((key) => settings[key])
    .filter((setting) => setting?.updated_by)
    .sort((first, second) => second.updated_at.localeCompare(first.updated_at));
  const newest = savedByAdmins[0];
  if (!newest) {
    return "Using the starting values";
  }
  return `Last saved ${formatSavedAt(newest.updated_at, timeZone)} by ${newest.updated_by}`;
}
