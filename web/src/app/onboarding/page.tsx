import Link from "next/link";

import { OnboardingFlow } from "@/components/OnboardingFlow";
import { ZephLogo } from "@/components/ZephLogo";

/**
 * The onboarding page a new User sees after sign-up, before the Dashboard.
 *
 * @returns The page.
 */
export default function OnboardingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <span aria-hidden="true" className="brand-stripe block h-0.5" />
      <header className="mx-auto flex w-full max-w-[1200px] items-center justify-between gap-4 px-4 py-5">
        <Link
          href="/"
          aria-label="Zeph home"
          className="flex items-center gap-2.5 text-ink no-underline"
        >
          <ZephLogo size={28} />
          <span className="text-2xl">Zeph</span>
        </Link>
      </header>
      <main className="mx-auto flex w-full max-w-[680px] flex-1 flex-col px-4 pb-12 pt-4">
        <OnboardingFlow />
      </main>
    </div>
  );
}
