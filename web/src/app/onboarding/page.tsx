import type { Metadata } from "next";

import { OnboardingFlow } from "@/components/OnboardingFlow";
import { SiteLoadFailed } from "@/components/SiteLoadFailed";
import { pageMetadata } from "@/lib/copy";
import { hasDesignFlag } from "@/lib/design-flags";
import { loadCopy } from "@/lib/server-copy";

/**
 * The onboarding page's browser tab title and search description, from
 * Copy. When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  if (!copy) {
    return {};
  }
  return pageMetadata(copy, "onboarding");
}

/**
 * The onboarding page a new User sees after sign-up, before the Dashboard,
 * worded by Copy read on the server. In design-fixture mode,
 * `?design=all-steps` stacks every step for the pixel test.
 *
 * @param props - `searchParams` is the page's query string.
 * @returns The page, or the error state when Copy can't be read.
 */
export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const copy = await loadCopy();
  if (!copy) {
    return <SiteLoadFailed />;
  }
  const { design } = await searchParams;
  const query = new URLSearchParams(
    typeof design === "string" ? { design } : {},
  );
  return (
    <main>
      <OnboardingFlow
        copy={copy}
        showAllSteps={hasDesignFlag(query, "all-steps")}
      />
    </main>
  );
}
