import { LandingPricing } from "@/components/LandingPricing";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import type { Copy } from "@/lib/copy";

/**
 * The public Pricing page, which every pricing link opens so it works
 * signed in too: the site header, Landing's pricing section as drawn, and
 * the footer. The design has no file of its own for it.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The page.
 */
export function Pricing({ copy }: { copy: Copy }) {
  return (
    <>
      <SiteHeader />
      <LandingPricing copy={copy} />
      <SiteFooter />
    </>
  );
}
