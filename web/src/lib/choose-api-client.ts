import { createApiClient, type ApiClient } from "@/lib/api-client";
import {
  createFixtureClient,
  readDesignAs,
} from "@/lib/design-fixtures/fixture-client";

/** What decides which API client the Dashboard gets. */
export type ApiClientSettings = {
  apiUrl: string;
  designFixtures: boolean;
};

/**
 * Picks the API client: the design-fixture client when fixture mode is on,
 * otherwise the real one.
 *
 * `process.env.NODE_ENV` is read here on purpose, outside the `env` module,
 * repeating the check in `designFixturesOn`: the build only drops the fixture
 * client when the literal check sits in this `if`. Without it, a production
 * bundle still contains the fixture code.
 *
 * @param settings - The backend's address and whether fixture mode is on.
 * @param getToken - Returns the signed-in User's session token.
 * @param cookies - The browser's cookies, read only in fixture mode.
 * @returns The API client.
 */
export function chooseApiClient(
  settings: ApiClientSettings,
  getToken: () => Promise<string | null>,
  cookies: string,
): ApiClient {
  if (process.env.NODE_ENV !== "production" && settings.designFixtures) {
    return createFixtureClient(readDesignAs(cookies));
  }
  return createApiClient(settings.apiUrl, getToken);
}
