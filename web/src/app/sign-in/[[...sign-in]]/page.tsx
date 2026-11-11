import { SignIn } from "@clerk/nextjs";

import { AuthLayout } from "@/components/AuthLayout";

/**
 * The sign-in page: Clerk's prebuilt sign-in, themed with the design tokens.
 *
 * @returns The page.
 */
export default function SignInPage() {
  return (
    <AuthLayout>
      <SignIn fallbackRedirectUrl="/" signUpUrl="/sign-up" />
    </AuthLayout>
  );
}
