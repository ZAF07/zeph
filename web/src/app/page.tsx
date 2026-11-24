import type { Metadata } from "next";

import { DashboardFrame } from "@/components/DashboardFrame";
import { DashboardHome } from "@/components/DashboardHome";
import { Landing } from "@/components/Landing";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { isSignedIn } from "@/lib/auth/server";
import { pageMetadata, pickCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The browser tab title and search description of `/`, from Copy: Home's
 * when signed in, Landing's when signed out. When Copy can't be read, the
 * root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, (await isSignedIn()) ? "home" : "landing");
}

/**
 * The `/` page: Landing for signed-out people, and the Dashboard home a
 * User lands on after onboarding for signed-in ones. Both read Copy on the
 * server; Home gets only the slots it shows: its own, onboarding's
 * Check-in frequency names and the Shared Memory-off notes.
 *
 * @returns The page, or the error state when Copy can't be read.
 */
export default async function RootPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  if (await isSignedIn()) {
    return (
      <DashboardFrame>
        <DashboardHome
          copy={pickCopy(copy, [
            "home.",
            "onboarding.check_ins.frequency_",
            "shared.memory_off.",
            "shared.pattern_noticing.",
          ])}
        />
      </DashboardFrame>
    );
  }
  return <Landing copy={copy} />;
}
