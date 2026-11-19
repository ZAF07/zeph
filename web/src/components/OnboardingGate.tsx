"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { readCopy, type Copy } from "@/lib/copy";
import { useMe } from "@/lib/queries";

/**
 * Shows the Dashboard only to Users who have finished onboarding; anyone
 * else is sent to onboarding first.
 *
 * @param props - `copy` is the frame's Copy; `children` is the Dashboard page.
 * @returns The page, a loading block, or an error with Try again.
 */
export function OnboardingGate({
  copy,
  children,
}: {
  copy: Copy;
  children: ReactNode;
}) {
  const text = (key: string) => readCopy(copy, `shared.dashboard.${key}`);
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
        title={text("load_failed.title")}
        body={text("load_failed.body")}
        retryLabel={text("load_failed.retry")}
        onRetry={() => void me.refetch()}
      />
    );
  }

  return <LoadingPanel shape="banner" label={text("loading")} />;
}
