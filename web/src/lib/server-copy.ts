import { cookies } from "next/headers";
import { cache } from "react";

import { env, serverApiUrl } from "@/env";
import { chooseApiClient } from "@/lib/choose-api-client";
import type { Copy } from "@/lib/copy";

/**
 * Loads the website's Copy while a public page renders on the server, so
 * signed-out visitors get it with no sign-in. It is read once per request,
 * however many parts of the page ask, and never kept between requests, so a
 * saved change shows on the next page load. Reading the request's cookies
 * also keeps the page from being built ahead of time with old Copy; in
 * design-fixture mode they say who to sign in as.
 *
 * @returns The Copy, or null when the backend couldn't be reached or
 *   refused, so the page can show its error state.
 */
export const loadCopy = cache(async (): Promise<Copy | null> => {
  const requestCookies = await cookies();
  const apiClient = chooseApiClient(
    { apiUrl: serverApiUrl(), designFixtures: env.designFixtures },
    async () => null,
    requestCookies.toString(),
  );
  try {
    return await apiClient.getCopy();
  } catch (error) {
    console.error("Couldn’t load the website Copy", error);
    return null;
  }
});
