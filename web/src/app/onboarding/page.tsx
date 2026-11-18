import { OnboardingFlow } from "@/components/OnboardingFlow";
import { hasDesignFlag } from "@/lib/design-flags";

/**
 * The onboarding page a new User sees after sign-up, before the Dashboard.
 * In design-fixture mode, `?design=all-steps` stacks every step for the
 * pixel test.
 *
 * @param props - `searchParams` is the page's query string.
 * @returns The page.
 */
export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { design } = await searchParams;
  const query = new URLSearchParams(
    typeof design === "string" ? { design } : {},
  );
  return (
    <main>
      <OnboardingFlow showAllSteps={hasDesignFlag(query, "all-steps")} />
    </main>
  );
}
