import { LandingPricing } from "@/components/LandingPricing";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

/**
 * The public Pricing page, which every pricing link opens so it works
 * signed in too: the site header, Landing's pricing section as drawn, and
 * the footer. The design has no file of its own for it.
 *
 * @returns The page.
 */
export function Pricing() {
  return (
    <>
      <SiteHeader />
      <LandingPricing />
      <SiteFooter />
    </>
  );
}
