"use client";

import { useAuth } from "@clerk/nextjs";

/**
 * Gives client components a way to get the signed-in User's session token.
 *
 * @returns A function that resolves to the token, or null when signed out.
 */
export function useSessionToken(): () => Promise<string | null> {
  const { getToken } = useAuth();
  return getToken;
}
