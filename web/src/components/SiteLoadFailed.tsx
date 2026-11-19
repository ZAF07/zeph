"use client";

import { useRouter } from "next/navigation";

import { LoadFailed } from "@/components/LoadFailed";
import { siteColumn } from "@/components/site-styles";

/**
 * What a public page shows when the website's Copy couldn't be read: the
 * shared couldn't-load block, with Try again loading the page afresh. Its
 * words can't come from Copy, since Copy is what failed to load.
 *
 * @returns The error state.
 */
export function SiteLoadFailed() {
  const router = useRouter();
  return (
    <main className={`${siteColumn} py-14`}>
      <LoadFailed
        title="Couldn’t load this page"
        body="Check your connection, then try again."
        onRetry={() => router.refresh()}
      />
    </main>
  );
}
