import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { DashboardShell } from "@/components/DashboardShell";
import { OnboardingGate } from "@/components/OnboardingGate";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { isSignedIn } from "@/lib/auth/server";
import { pickCopy } from "@/lib/copy";
import { isMenuFoldedCookie, MENU_FOLDED_COOKIE } from "@/lib/menu-fold";
import { loadCopy } from "@/lib/server-copy";

/**
 * The Dashboard frame around User and admin pages alike. Signed-out people
 * are sent to sign-in, and Users who have not finished onboarding are sent
 * there first. The fold cookie decides whether the sidebar is drawn folded
 * from the first paint. The menu's words are Copy, read on the server; only
 * the frame's slots go to the browser.
 *
 * @param props - `children` is the page.
 * @returns The page in its frame, or the error state when Copy can't be
 *   read.
 */
export async function DashboardFrame({ children }: { children: ReactNode }) {
  if (!(await isSignedIn())) {
    redirect("/sign-in");
  }
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  const frameCopy = pickCopy(copy, ["shared.dashboard.", "shared.wordmark"]);
  const menuFolded = isMenuFoldedCookie(
    (await cookies()).get(MENU_FOLDED_COOKIE)?.value,
  );
  return (
    <DashboardShell copy={frameCopy} initialMenuFolded={menuFolded}>
      <OnboardingGate copy={frameCopy}>{children}</OnboardingGate>
    </DashboardShell>
  );
}
