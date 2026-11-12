"use client";

import { useAuth, useClerk } from "@clerk/nextjs";

/**
 * Gives client components a way to get the signed-in User's session token.
 *
 * @returns A function that resolves to the token, or null when signed out.
 */
export function useSessionToken(): () => Promise<string | null> {
  const { getToken } = useAuth();
  return getToken;
}

/**
 * Gives client components a way to sign the User out.
 *
 * @returns A function that signs out, then opens the given page.
 */
export function useSignOut(): (redirectUrl: string) => Promise<void> {
  const { signOut } = useClerk();
  return (redirectUrl) => signOut({ redirectUrl });
}
