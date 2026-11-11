"use client";

import { useEffect, useState } from "react";

import { useApiClient } from "@/lib/use-api-client";

/**
 * Tells client components whether the signed-in User is an Admin, so they
 * can show the admin area. The backend still checks every admin request.
 *
 * @returns True once the User is known to be an Admin; false until then.
 */
export function useIsAdmin(): boolean {
  const apiClient = useApiClient();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    apiClient
      .getMe()
      .then((me) => setIsAdmin(me.role === "admin"))
      .catch(() => setIsAdmin(false));
  }, [apiClient]);

  return isAdmin;
}
