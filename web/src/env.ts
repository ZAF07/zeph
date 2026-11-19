import { PHASE_PRODUCTION_BUILD } from "next/constants";

/**
 * Reads a required setting, failing loudly with the key's name.
 *
 * @param key - The environment variable name, used in the error message.
 * @param value - The value read for that key.
 * @returns The value.
 */
function required(key: string, value: string | undefined): string {
  if (!value) {
    throw new Error(`Missing required setting in .env: ${key}`);
  }
  return value;
}

/**
 * Says whether design-fixture mode is on (ADR 0018): only when
 * `NEXT_PUBLIC_DESIGN_FIXTURES=1`, and never in a production build.
 *
 * @param nodeEnv - `NODE_ENV`, which Next.js sets to "production" when building.
 * @param flag - The value of `NEXT_PUBLIC_DESIGN_FIXTURES`.
 * @returns True when the Dashboard should run on design fixtures.
 */
export function designFixturesOn(
  nodeEnv: string | undefined,
  flag: string | undefined,
): boolean {
  return nodeEnv !== "production" && flag === "1";
}

/**
 * Public settings for the Dashboard, read once from the environment.
 *
 * Next.js only inlines `NEXT_PUBLIC_*` keys when they are written out in full,
 * so each key is named literally here.
 */
export const env = {
  apiUrl: required("NEXT_PUBLIC_API_URL", process.env.NEXT_PUBLIC_API_URL),
  clerkPublishableKey: required(
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  ),
  designFixtures: designFixturesOn(
    process.env.NODE_ENV,
    process.env.NEXT_PUBLIC_DESIGN_FIXTURES,
  ),
};

/**
 * The backend's address as the Dashboard's own server reaches it, for pages
 * that load data while rendering on the server. Inside Docker the browser's
 * address (`NEXT_PUBLIC_API_URL`) points at the host, so the stack sets
 * `SERVER_API_URL` to the backend's address on the Docker network. Without
 * it, the browser's address is used.
 *
 * @returns The backend's address for server-side calls.
 */
export function serverApiUrl(): string {
  return process.env.SERVER_API_URL || env.apiUrl;
}

/**
 * Stops the Dashboard server from starting when a server-only key is missing.
 * Called from `next.config.ts`; Clerk reads the key itself at request time.
 * Skipped while `next build` runs, so the image is built without the secret.
 *
 * @param phase - The Next.js phase the config is loaded for.
 */
export function checkServerSettings(phase: string): void {
  if (phase === PHASE_PRODUCTION_BUILD) {
    return;
  }
  required("CLERK_SECRET_KEY", process.env.CLERK_SECRET_KEY);
}
