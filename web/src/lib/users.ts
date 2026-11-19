import type { UserRole } from "@/lib/api-client";

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
