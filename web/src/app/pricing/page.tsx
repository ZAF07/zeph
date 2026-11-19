import type { Metadata } from "next";

import { Pricing } from "@/components/Pricing";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { pageMetadata } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The browser tab title and search description of Pricing, from Copy.
 * When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, "pricing");
}

/**
 * The public Pricing page. Every word on it is Copy.
 *
 * @returns The page, or the error state when Copy can't be read.
 */
export default async function PricingPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  return <Pricing copy={copy} />;
}
