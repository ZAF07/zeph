import { SignUp } from "@clerk/nextjs";
import type { Metadata } from "next";

import { AuthLayout } from "@/components/AuthLayout";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { pageMetadata } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The sign-up page's browser tab title and search description, from Copy.
 * When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, "auth.sign_up");
}

/**
 * The sign-up page: Clerk's prebuilt sign-up, themed with the design tokens,
 * framed by words from Copy.
 *
 * @returns The page, or the error state when Copy can't be read.
 */
export default async function SignUpPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  return (
    <AuthLayout copy={copy} page="sign_up">
      <SignUp forceRedirectUrl="/connect-telegram" signInUrl="/sign-in" />
    </AuthLayout>
  );
}
