import type { Metadata } from "next";

import { HowItWorks } from "@/components/HowItWorks";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { pageMetadata } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The browser tab title and search description of How It Works, from Copy.
 * When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, "how_it_works");
}

/**
 * The public How It Works page.
 *
 * @returns The page, or the error state when Copy can't be read.
 */
export default async function HowItWorksPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  return <HowItWorks copy={copy} />;
}
