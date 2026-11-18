import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { DashboardShell } from "@/components/DashboardShell";
import { OnboardingGate } from "@/components/OnboardingGate";
import { isSignedIn } from "@/lib/auth/server";
import { isMenuFoldedCookie, MENU_FOLDED_COOKIE } from "@/lib/menu-fold";

/**
 * The Dashboard frame around User and admin pages alike. Signed-out people
 * are sent to sign-in, and Users who have not finished onboarding are sent
 * there first. The fold cookie decides whether the sidebar is drawn folded
 * from the first paint.
 *
 * @param props - `children` is the page.
 * @returns The page in its frame.
 */
export async function DashboardFrame({ children }: { children: ReactNode }) {
  if (!(await isSignedIn())) {
    redirect("/sign-in");
  }
  const menuFolded = isMenuFoldedCookie(
    (await cookies()).get(MENU_FOLDED_COOKIE)?.value,
  );
  return (
    <DashboardShell initialMenuFolded={menuFolded}>
      <OnboardingGate>{children}</OnboardingGate>
    </DashboardShell>
  );
}
