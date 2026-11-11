import { SignUp } from "@clerk/nextjs";

import { AuthLayout } from "@/components/AuthLayout";

/**
 * The sign-up page: Clerk's prebuilt sign-up, themed with the design tokens.
 *
 * @returns The page.
 */
export default function SignUpPage() {
  return (
    <AuthLayout>
      <SignUp forceRedirectUrl="/connect-telegram" signInUrl="/sign-in" />
    </AuthLayout>
  );
}
