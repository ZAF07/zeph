import type { FeatureReason } from "@/lib/api-client";
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
  on_for_everyone: "On: on for everyone",
  on_for_user: "On: turned on for this User",
  off_for_everyone: "Off: turned off for everyone",
  off_for_user: "Off: turned off for this User",
  turned_off_by_user: "Off: the User turned it off",
};

/**
 * Says in plain words whether a Feature works for a User, and why.
 *
 * @param reason - Why it works or doesn't.
 * @returns A line like "Off: turned off for everyone".
 */
export function reasonText(reason: FeatureReason): string {
  return reasonTexts[reason];
}
