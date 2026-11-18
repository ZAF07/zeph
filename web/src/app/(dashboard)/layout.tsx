import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { DashboardShell } from "@/components/DashboardShell";
import { OnboardingGate } from "@/components/OnboardingGate";
import { isSignedIn } from "@/lib/auth/server";

/**
 * The Dashboard frame around User and admin pages alike. Users who have not
 * finished onboarding are sent there first.
 *
 * @param props - `children` is the page.
 * @returns The page in its frame.
 */
export default async function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  if (!(await isSignedIn())) {
    redirect("/sign-in");
  }
  return (
    <DashboardShell>
      <OnboardingGate>{children}</OnboardingGate>
    </DashboardShell>
  );
}
