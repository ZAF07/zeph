import type { Metadata } from "next";

import { DashboardFrame } from "@/components/DashboardFrame";
import { DashboardHome } from "@/components/DashboardHome";
import { Landing } from "@/components/Landing";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { isSignedIn } from "@/lib/auth/server";
import { readCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The browser tab title and search description of `/`. Signed out, they
 * are Landing's, from Copy; signed in, or when Copy can't be read, the
 * root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  if (await isSignedIn()) {
    return {};
  }
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return {
    title: readCopy(copy, "landing.page_title"),
    description: readCopy(copy, "landing.page_description"),
  };
}

/**
 * The `/` page: Landing for signed-out people, and the Dashboard home a
 * User lands on after onboarding for signed-in ones.
 *
 * @returns The page.
 */
export default async function RootPage() {
  if (await isSignedIn()) {
    return (
      <DashboardFrame>
        <DashboardHome />
      </DashboardFrame>
    );
  }
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  return <Landing copy={copy} />;
}
