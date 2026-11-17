import { auth } from "@clerk/nextjs/server";

/**
 * Tells server components whether someone is signed in. It reads Clerk's
 * session from the request, so it makes no call to Clerk.
 *
 * @returns True when someone is signed in.
 */
export async function isSignedIn(): Promise<boolean> {
  const { userId } = await auth();
  return userId !== null;
}
