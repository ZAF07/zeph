import { SignIn } from "@clerk/nextjs";
import type { Metadata } from "next";

import { AuthLayout } from "@/components/AuthLayout";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { pageMetadata } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The sign-in page's browser tab title and search description, from Copy.
 * When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, "auth.sign_in");
}

/**
 * The sign-in page: Clerk's prebuilt sign-in, themed with the design tokens,
 * framed by words from Copy.
 *
 * @returns The page, or the error state when Copy can't be read.
 */
export default async function SignInPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  return (
    <AuthLayout copy={copy} page="sign_in">
      <SignIn fallbackRedirectUrl="/" signUpUrl="/sign-up" />
    </AuthLayout>
  );
}
