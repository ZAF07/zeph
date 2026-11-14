"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { LoadFailed } from "@/components/LoadFailed";
import { useMe } from "@/lib/queries";

/**
 * Shows admin pages only to Admins; anyone else is sent home. The backend
 * refuses non-Admins too, so this only keeps the admin area out of sight.
 *
 * @param props - `children` is the admin page.
 * @returns The page, a loading block, or an error with Try again.
 */
export function AdminGate({ children }: { children: ReactNode }) {
  const me = useMe();
  const router = useRouter();
  const isNotAdmin = me.data !== undefined && me.data.role !== "admin";

  useEffect(() => {
    if (isNotAdmin) {
      router.replace("/");
    }
  }, [isNotAdmin, router]);

  if (me.data?.role === "admin") {
    return <>{children}</>;
  }

  if (me.isError) {
    return (
      <LoadFailed
        title="Couldn’t open the admin area"
        body="Nothing has changed. Try again in a moment."
        onRetry={() => void me.refetch()}
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
