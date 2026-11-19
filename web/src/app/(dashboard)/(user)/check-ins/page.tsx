import type { Metadata } from "next";

import { CheckInsSettings } from "@/components/CheckInsSettings";
import { CopyLoadFailed } from "@/components/CopyLoadFailed";
import { pageMetadata, pickCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The Check-ins page's browser tab title and search description, from
 * Copy. When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  return copy ? pageMetadata(copy, "check_ins") : {};
}

/**
 * The Check-ins page, where a User sets up, pauses and reviews Check-ins.
 * Its words come from Copy, read on the server; only its slots and
 * onboarding's frequency names go to the browser.
 *
 * @returns The page, or the couldn't-load block when Copy can't be read.
 */
export default async function CheckInsPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <CopyLoadFailed />;
  }
  return (
    <CheckInsSettings
      copy={pickCopy(copy, ["check_ins.", "onboarding.check_ins.frequency_"])}
    />
  );
}
