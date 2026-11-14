"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { secondaryButton } from "@/components/button-styles";
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
      <div
        role="alert"
        className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-danger-line bg-danger-tint p-4 text-danger-deep"
      >
        <span className="text-sm">
          We couldn’t load this. Nothing you’ve shared is lost.
        </span>
        <button
          type="button"
          className={`${secondaryButton} bg-white`}
          onClick={() => void me.refetch()}
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div
      aria-busy="true"
      className="h-[200px] rounded-card border border-line bg-subtle"
    />
  );
}
