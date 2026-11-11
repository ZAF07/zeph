import { ClerkProvider } from "@clerk/nextjs";
import type { ReactNode } from "react";

import { env } from "@/env";
import { clerkAppearance } from "@/lib/auth/clerk-appearance";

/**
 * Makes sign-in available to every page, with Clerk themed by the design
 * tokens. Keeps Clerk inside the auth helper.
 *
 * @param props - `children` is the app.
 * @returns The provider wrapping the app.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider
      appearance={clerkAppearance}
      publishableKey={env.clerkPublishableKey}
    >
      {children}
    </ClerkProvider>
  );
}
