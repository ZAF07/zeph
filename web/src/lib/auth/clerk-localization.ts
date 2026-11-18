import type { ComponentProps } from "react";
import type { ClerkProvider } from "@clerk/nextjs";

/**
 * The copy Clerk shows on the sign-in and sign-up pages, from the design's
 * `Login` and `Signup` files.
 */
export const clerkLocalization: ComponentProps<
  typeof ClerkProvider
>["localization"] = {
  signIn: {
    start: {
      title: "Sign in to Zeph",
      subtitle:
        "Your memories, check-ins and account live here. The conversation itself happens in Telegram.",
    },
  },
  signUp: {
    start: {
      title: "Create your account",
      subtitle:
        "Sign up here, answer a few short questions, then meet Zeph in Telegram.",
    },
  },
  formFieldInputPlaceholder__emailAddress: "you@example.com",
};
