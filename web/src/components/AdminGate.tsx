"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { LoadFailed } from "@/components/LoadFailed";
import { useApiClient } from "@/lib/use-api-client";

type GateState = "checking" | "admin" | "failed";

/**
 * Shows admin pages only to Admins; anyone else is sent home. The backend
 * refuses non-Admins too, so this only keeps the admin area out of sight.
 *
 * @param props - `children` is the admin page.
 * @returns The page, a loading block, or an error with Try again.
 */
export function AdminGate({ children }: { children: ReactNode }) {
  const apiClient = useApiClient();
  const router = useRouter();
  const [state, setState] = useState<GateState>("checking");

  const check = useCallback(async () => {
    setState("checking");
    try {
      const me = await apiClient.getMe();
      if (me.role === "admin") {
        setState("admin");
      } else {
        router.replace("/");
      }
    } catch {
      setState("failed");
    }
  }, [apiClient, router]);

  useEffect(() => {
    void check();
  }, [check]);

  if (state === "admin") {
    return <>{children}</>;
  }

  if (state === "failed") {
    return (
      <LoadFailed
        title="Couldn’t open the admin area"
        body="Nothing has changed. Try again in a moment."
        onRetry={() => void check()}
      />
    );
  }

  return (
    <div
      aria-busy="true"
      className="h-[200px] rounded-card border border-line bg-subtle"
    />
  );
}
