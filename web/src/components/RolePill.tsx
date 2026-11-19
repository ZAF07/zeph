import { StatusPill } from "@/components/StatusPill";
import type { UserRole } from "@/lib/api-client";

/**
 * A User's role as a pill: cream for an Admin, outlined for a User.
 *
 * @param props - `role` is the User's role.
 * @returns The pill.
 */
export function RolePill({ role }: { role: UserRole }) {
  return (
    <StatusPill filled={role === "admin"}>
      {role === "admin" ? "Admin" : "User"}
    </StatusPill>
  );
}
