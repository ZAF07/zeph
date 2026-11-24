import type {
  FeatureReason,
  UserFeatureStatus,
  UserFeatureSwitch,
} from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";

/**
 * Says who last changed a Feature's switch, and when.
 *
 * @param change - When it was last changed and the Admin's email, each null
 *   if unknown.
 * @returns A note like "Changed 13 Nov, 14:20 by maya@example.com", or
 *   "Never changed".
 */
export function lastChangeNote(change: {
  changed_at: string | null;
  changed_by_email: string | null;
}): string {
  if (!change.changed_at) {
    return "Never changed";
  }
  const changedBy = change.changed_by_email
    ? ` by ${change.changed_by_email}`
    : "";
  return `Changed ${formatSavedAt(change.changed_at)}${changedBy}`;
}

const reasonTexts: Record<FeatureReason, string> = {
  on_for_everyone: "Works: on for everyone",
  on_for_user: "Works: on for this user",
  off_for_everyone: "Off for everyone",
  off_for_user: "Off for this user",
  turned_off_by_user: "Off: the user turned it off",
  stickers_off: "Off: Stickers is off for this user",
  pattern_noticing_off: "Off: Pattern noticing is off for this user",
};

/**
 * Says in plain words whether a Feature works for a User, and why, as the
 * Users panel shows it. The Stickers line says how many Personal Stickers
 * the User keeps (never which) in place of the reason when it works.
 *
 * @param status - The Feature's status for the User.
 * @param personalStickerCount - How many Personal Stickers the User keeps.
 * @returns A line like "Works: on for everyone" or "Works · 4 personal
 *   stickers kept".
 */
export function userFeatureLine(
  status: UserFeatureStatus,
  personalStickerCount: number,
): string {
  if (status.feature !== "stickers") {
    return reasonTexts[status.reason];
  }
  const stickers = `${personalStickerCount} personal sticker${
    personalStickerCount === 1 ? "" : "s"
  } kept`;
  const state = status.works ? "Works" : reasonTexts[status.reason];
  return `${state} · ${stickers}`;
}

/**
 * Tells whether an Admin's switch lets a Feature work for a User.
 *
 * @param featureSwitch - The switch for the User.
 * @param isOnForEveryone - Whether the Feature is on for everyone.
 * @returns True when it is on for the User.
 */
export function isOnForUser(
  featureSwitch: UserFeatureSwitch,
  isOnForEveryone: boolean,
): boolean {
  return featureSwitch === "default" ? isOnForEveryone : featureSwitch === "on";
}

/**
 * Picks the switch to save when an Admin turns a Feature on or off for a
 * User: Default when that matches everyone's switch, otherwise On or Off.
 *
 * @param turnOn - Whether the Admin turned it on.
 * @param isOnForEveryone - Whether the Feature is on for everyone.
 * @returns The switch for the User.
 */
export function switchForUser(
  turnOn: boolean,
  isOnForEveryone: boolean,
): UserFeatureSwitch {
  if (turnOn === isOnForEveryone) {
    return "default";
  }
  return turnOn ? "on" : "off";
}
