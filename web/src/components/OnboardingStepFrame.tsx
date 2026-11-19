import Link from "next/link";
import type { ReactNode } from "react";

/**
 * The frame around one onboarding step: the Zeph wordmark over a centred
 * column. On the all-steps design sheet, every frame after the first has a
 * dashed line above it.
 *
 * @param props - `wordmark` and `homeLinkLabel` are the wordmark's words
 *   and the name screen readers give its home link; `hasSeparator` draws
 *   the dashed line; `children` is the step.
 * @returns The step's section.
 */
export function OnboardingStepFrame({
  wordmark,
  homeLinkLabel,
  hasSeparator = false,
  children,
}: {
  wordmark: string;
  homeLinkLabel: string;
  hasSeparator?: boolean;
  children: ReactNode;
}) {
  return (
    <section
      className={`box-border min-h-[700px] px-8 pb-16 pt-10 max-[899px]:px-5 ${
        hasSeparator ? "border-t border-dashed border-line-strong" : ""
      }`}
    >
      <div className="mx-auto flex max-w-[560px] flex-col gap-[22px]">
        <Link
          href="/"
          aria-label={homeLinkLabel}
          className="self-start text-[26px] font-normal text-cream"
        >
          {wordmark}
        </Link>
        {children}
      </div>
    </section>
  );
}
