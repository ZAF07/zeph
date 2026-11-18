"use client";

import { useMemo } from "react";

import { env } from "@/env";
import type { ApiClient } from "@/lib/api-client";
import { useSessionToken } from "@/lib/auth/client";
import { chooseApiClient } from "@/lib/choose-api-client";

/**
 * Gives client components the API client, signed in as the current User.
 *
 * @returns The API client.
 */
export function useApiClient(): ApiClient {
  const getToken = useSessionToken();
  return useMemo(
    () =>
      chooseApiClient(
        env,
        getToken,
        typeof document === "undefined" ? "" : document.cookie,
      ),
    [getToken],
  );
}
