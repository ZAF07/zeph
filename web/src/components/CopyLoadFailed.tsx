"use client";

import { useRouter } from "next/navigation";

import { LoadFailed } from "@/components/LoadFailed";

/**
 * The shared couldn't-load block for when the website's Copy couldn't be
 * read, with Try again loading the page afresh. Its words can't come from
 * Copy, since Copy is what failed to load.
 *
 * @returns The error block.
 */
export function CopyLoadFailed() {
  const router = useRouter();
  return (
    <LoadFailed
      title="Couldn’t load this page"
      body="Check your connection, then try again."
      onRetry={() => router.refresh()}
    />
  );
}
