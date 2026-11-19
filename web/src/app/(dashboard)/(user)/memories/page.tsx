import type { Metadata } from "next";

import { CopyLoadFailed } from "@/components/CopyLoadFailed";
import { Memories } from "@/components/Memories";
import { pageMetadata, pickCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The Memories page's browser tab title and search description, from
 * Copy. When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, "memories");
}

/**
 * The Memories page, where a User sees and deletes what Zeph remembers.
 * Its words come from Copy, read on the server; only its slots go to the
 * browser.
 *
 * @returns The page, or the couldn't-load block when Copy can't be read.
 */
export default async function MemoriesPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <CopyLoadFailed />;
  }
  return <Memories copy={pickCopy(copy, ["memories."])} />;
}
