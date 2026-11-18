import { SignUp } from "@clerk/nextjs";

import { AuthLayout } from "@/components/AuthLayout";

/**
 * The sign-up page: Clerk's prebuilt sign-up, themed with the design tokens.
 *
 * @returns The page.
 */
export default function SignUpPage() {
  return (
    <AuthLayout
      eyebrow="Get started"
      switchPrompt="Have an account?"
      switchLink={{ href: "/sign-in", label: "Sign in" }}
    >
      <SignUp forceRedirectUrl="/connect-telegram" signInUrl="/sign-in" />
    </AuthLayout>
  );
}
