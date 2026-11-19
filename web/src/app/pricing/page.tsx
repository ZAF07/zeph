import { Pricing } from "@/components/Pricing";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { loadCopy } from "@/lib/server-copy";

/**
 * The public Pricing page. Its plans' words are Landing's pricing Copy.
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
