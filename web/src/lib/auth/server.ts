import { currentUser } from "@clerk/nextjs/server";

/** The signed-in person, as shown in the Dashboard shell. */
export type CurrentAccount = {
  name: string;
  email: string;
};

/**
 * Looks up the signed-in person for server components.
 *
 * @returns Their name and email, or null when nobody is signed in.
 */
export async function getCurrentAccount(): Promise<CurrentAccount | null> {
  const user = await currentUser();
  if (!user) {
    return null;
  }
  const email = user.primaryEmailAddress?.emailAddress ?? "";
  const name = user.fullName || user.firstName || email;
  return { name, email };
}
