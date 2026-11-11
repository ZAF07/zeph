"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { secondaryButton } from "@/components/button-styles";
import { useApiClient } from "@/lib/use-api-client";

type GateState = "checking" | "onboarded" | "failed";

/**
 * Shows the Dashboard only to Users who have finished onboarding; anyone
 * else is sent to onboarding first.
 *
 * @param props - `children` is the Dashboard page.
 * @returns The page, a loading block, or an error with Try again.
 */
export function OnboardingGate({ children }: { children: ReactNode }) {
  const apiClient = useApiClient();
  const router = useRouter();
  const [state, setState] = useState<GateState>("checking");

  const check = useCallback(async () => {
    setState("checking");
    try {
      const me = await apiClient.getMe();
      if (me.onboarding_completed_at) {
        setState("onboarded");
      } else {
        router.replace("/onboarding");
      }
    } catch {
      setState("failed");
    }
  }, [apiClient, router]);

  useEffect(() => {
    void check();
  }, [check]);

  if (state === "onboarded") {
    return <>{children}</>;
  }

  if (state === "failed") {
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
          onClick={() => void check()}
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
