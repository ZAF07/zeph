import type { ApiClient } from "@/lib/api-client";
import { accountFixtures } from "@/lib/design-fixtures/account";
import { adminCardsFixtures } from "@/lib/design-fixtures/admin-cards";
import { adminFormsFixtures } from "@/lib/design-fixtures/admin-forms";
import { adminTablesFixtures } from "@/lib/design-fixtures/admin-tables";
import { adminUsersFixtures } from "@/lib/design-fixtures/admin-users";
import { checkInsFixtures } from "@/lib/design-fixtures/check-ins";
import { copyFixtures } from "@/lib/design-fixtures/copy";
import { evalDaySummaryFixtures } from "@/lib/design-fixtures/eval-day-summary";
import { homeFixtures } from "@/lib/design-fixtures/home";
import { memoriesFixtures } from "@/lib/design-fixtures/memories";
import { modelCallTraceFixtures } from "@/lib/design-fixtures/model-call-trace";
import { onboardingFixtures } from "@/lib/design-fixtures/onboarding";
import { overviewFixtures } from "@/lib/design-fixtures/overview";
import { planFixtures } from "@/lib/design-fixtures/plan";
import { alex, shellFixtures, zaf } from "@/lib/design-fixtures/shell";
import { telegramFixtures } from "@/lib/design-fixtures/telegram";

/** Who the design fixtures sign in as: Alex the User, or Zaf the Admin. */
export type DesignAs = "user" | "admin";

/**
 * The cookie that asks the design fixtures to sign in as Zaf. The
 * run-dashboard skill's save-state.mjs sets the same name.
 */
const DESIGN_AS_COOKIE = "zeph-design-as";

/**
 * Reads who to sign in as from the browser's cookies.
 *
 * @param cookies - The `document.cookie` string.
 * @returns "admin" when `zeph-design-as=admin` is set, otherwise "user".
 */
export function readDesignAs(cookies: string): DesignAs {
  const isAdmin = cookies
    .split(";")
    .some((cookie) => cookie.trim() === `${DESIGN_AS_COOKIE}=admin`);
  return isAdmin ? "admin" : "user";
}

/**
 * Turns the fixtures into a full client. A call with no fixture yet fails
 * with an error naming it, so a page shows its error state rather than
 * calling the backend. `then` is left alone so the client is never mistaken
 * for a promise.
 *
 * @param fixtures - The calls that have fixture data.
 * @returns A client with the same interface as the real one.
 */
function withMissingFixturesFailing(fixtures: Partial<ApiClient>): ApiClient {
  return new Proxy(fixtures, {
    get(target, name) {
      const fixture: unknown = Reflect.get(target, name);
      if (
        fixture !== undefined ||
        typeof name !== "string" ||
        name === "then"
      ) {
        return fixture;
      }
      return () =>
        Promise.reject(new Error(`No design fixture for ${name} yet`));
    },
  }) as ApiClient;
}

/**
 * Builds the API client for design-fixture mode (ADR 0018). It returns the
 * data drawn in `design/reference/` and never calls the backend. The shell's
 * signed-in User comes first, so a page area's file can replace it, as the
 * onboarding sheet does on its own address.
 *
 * @param designAs - Sign in as Alex the User, or Zaf the Admin.
 * @returns The fixture client.
 */
export function createFixtureClient(designAs: DesignAs): ApiClient {
  return withMissingFixturesFailing({
    ...shellFixtures(designAs === "admin" ? zaf : alex),
    ...homeFixtures,
    ...memoriesFixtures,
    ...checkInsFixtures,
    ...accountFixtures,
    ...telegramFixtures,
    ...onboardingFixtures(globalThis.location?.search ?? ""),
    ...adminUsersFixtures,
    ...adminTablesFixtures,
    ...modelCallTraceFixtures,
    ...adminFormsFixtures,
    ...adminCardsFixtures,
    ...planFixtures,
    ...overviewFixtures,
    ...copyFixtures,
    ...evalDaySummaryFixtures,
  });
}
