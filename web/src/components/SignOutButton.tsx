"use client";

import { secondaryButton } from "@/components/button-styles";
import { useSignOut } from "@/lib/auth/client";

/**
 * A button that signs the User out and takes them to the sign-in page.
 *
 * @returns The button.
 */
export function SignOutButton() {
  const signOut = useSignOut();

  return (
    <button
      type="button"
      className={secondaryButton}
      onClick={() => signOut("/sign-in")}
    >
      Sign out
    </button>
  );
}
