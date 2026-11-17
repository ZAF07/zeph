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
};

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
