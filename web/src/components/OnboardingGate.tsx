"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { useMe } from "@/lib/queries";

/**
 * Shows the Dashboard only to Users who have finished onboarding; anyone
 * else is sent to onboarding first.
 *
 * @param props - `children` is the Dashboard page.
 * @returns The page, a loading block, or an error with Try again.
 */
export function OnboardingGate({ children }: { children: ReactNode }) {
  const me = useMe();
  const router = useRouter();
  const isNotOnboarded =
    me.data !== undefined && !me.data.onboarding_completed_at;

  useEffect(() => {
    if (isNotOnboarded) {
      router.replace("/onboarding");
    }
  }, [isNotOnboarded, router]);

  if (me.data?.onboarding_completed_at) {
    return <>{children}</>;
  }

  if (me.isError) {
    return (
      <LoadFailed
        title="We couldn’t load this"
        body="Nothing you’ve shared is lost."
        onRetry={() => void me.refetch()}
      />
    );
  }

  return <LoadingPanel shape="banner" label="Loading your Dashboard" />;
}
