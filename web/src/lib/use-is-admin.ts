"use client";

import { useMe } from "@/lib/queries";

/**
 * Tells client components whether the signed-in User is an Admin, so they
 * can show the admin area. The backend still checks every admin request.
 *
 * @returns True once the User is known to be an Admin; false until then.
 */
export function useIsAdmin(): boolean {
  return useMe().data?.role === "admin";
}
