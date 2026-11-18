import { DashboardFrame } from "@/components/DashboardFrame";
import { DashboardHome } from "@/components/DashboardHome";
import { Landing } from "@/components/Landing";
import { isSignedIn } from "@/lib/auth/server";

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
  return <Landing />;
}
