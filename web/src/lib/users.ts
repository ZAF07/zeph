import type { PatternState, UserRole } from "@/lib/api-client";

/**
 * Names a User for admin messages: their name, else their email.
 *
 * @param user - The User's name and email, each null if unknown.
 * @returns Their name, else their email, else "This User".
 */
export function displayNameOf(user: {
  name: string | null;
  email: string | null;
}): string {
  return user.name ?? user.email ?? "This User";
}

/**
 * Says a role in plain words.
 *
 * @param role - The User's role.
 * @returns "Admin" or "User".
 */
export function roleLabel(role: UserRole): string {
  return role === "admin" ? "Admin" : "User";
}

/** Every Pattern state but confirmed, in order, with its row's label. */
const otherPatternStates: { state: PatternState; label: string }[] = [
  { state: "noticed", label: "Noticed Patterns" },
  { state: "suspected", label: "Suspected Patterns" },
  { state: "ready", label: "Ready Patterns" },
  { state: "shared", label: "Shared Patterns" },
  { state: "contested", label: "Contested Patterns" },
  { state: "closed", label: "Closed Patterns" },
  { state: "unmatched", label: "Unmatched Patterns" },
];

/** A User with no Patterns in any state. */
export const noPatterns: Record<PatternState, number> = {
  noticed: 0,
  suspected: 0,
  ready: 0,
  shared: 0,
  confirmed: 0,
  contested: 0,
  closed: 0,
  unmatched: 0,
};

/**
 * Lists a User's Pattern counts for the states other than confirmed, which
 * has its own row, leaving out any state they have none in.
 *
 * @param counts - How many Patterns they have in each state.
 * @returns A label and count for each state with at least one, in order.
 */
export function otherPatternCounts(
  counts: Record<PatternState, number>,
): { label: string; value: string }[] {
  return otherPatternStates
    .filter(({ state }) => counts[state] > 0)
    .map(({ state, label }) => ({ label, value: String(counts[state]) }));
}
