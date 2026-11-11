"use client";

import { useMemo } from "react";

import { env } from "@/env";
import { createApiClient, type ApiClient } from "@/lib/api-client";
import { useSessionToken } from "@/lib/auth/client";

/**
 * Gives client components the API client, signed in as the current User.
 *
 * @returns The API client.
 */
export function useApiClient(): ApiClient {
  const getToken = useSessionToken();
  return useMemo(() => createApiClient(env.apiUrl, getToken), [getToken]);
}
