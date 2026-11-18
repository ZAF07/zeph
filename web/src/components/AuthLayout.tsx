import Link from "next/link";
import type { ReactNode } from "react";

import { secondaryButton } from "@/components/button-styles";
import { PublicHeader } from "@/components/PublicHeader";

/**
 * The sign-in and sign-up page frame, from the design's `Login` and `Signup`
 * files: the archway picture behind the public header, a card holding the
 * eyebrow and the Clerk form, and the Terms, 18+ and AI companion lines.
 * The card carries `data-clerk-card`, which the pixel test masks.
 *
 * @param props - `eyebrow` is the small line above the form; `switchPrompt`
 *   and `switchLink` offer the other auth page in the header; `children` is
 *   the Clerk component.
 * @returns The page layout.
 */
export function AuthLayout({
  eyebrow,
  switchPrompt,
  switchLink,
  children,
}: {
  eyebrow: string;
  switchPrompt: string;
  switchLink: { href: string; label: string };
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-[800px] flex-col [background:linear-gradient(180deg,rgba(10,32,44,.25),rgba(10,32,44,.25)),url(/design/auth-archway.jpg)_left_bottom/cover_no-repeat_#0A202C] max-[899px]:min-h-[920px] max-[899px]:[background:linear-gradient(180deg,#0A202C_0%,#0A202C_calc(100%_-_390px),rgba(10,32,44,0)_calc(100%_-_260px)),url(/design/auth-archway.jpg)_left_bottom/auto_390px_no-repeat_#0A202C]">
      <PublicHeader
        actions={
          <>
            <span className="text-soft max-[899px]:hidden">{switchPrompt}</span>
            <Link href={switchLink.href} className={secondaryButton}>
              {switchLink.label}
            </Link>
          </>
        }
      />
      <main className="mx-auto box-border flex w-full max-w-[1160px] flex-1 flex-wrap items-center justify-end px-8 pt-10 pb-12 max-[899px]:items-start max-[899px]:justify-center max-[899px]:px-4 max-[899px]:pt-5 max-[899px]:pb-[270px]">
        <div className="mr-[clamp(0px,13vw,170px)] flex min-w-0 flex-[0_1_400px] flex-col gap-4 max-[899px]:mr-0">
          <div
            data-clerk-card
            className="box-border flex flex-col gap-[18px] rounded-banner border border-line bg-bg-deep/80 p-9 max-[899px]:px-[22px] max-[899px]:py-[26px]"
          >
            <div className="flex items-center gap-3 text-[11px] font-medium tracking-[2.5px] text-soft uppercase">
              <span aria-hidden="true" className="h-px w-[18px] bg-soft" />
              {eyebrow}
            </div>
            {children}
          </div>
          <p className="m-0 text-center text-[12px] text-soft">
            By continuing you agree to the <a href="/terms">Terms</a> and{" "}
            <a href="/privacy">Privacy policy</a>. You must be 18 or older to
            use Zeph.
          </p>
        </div>
      </main>
      <p className="m-0 px-8 pb-6 text-center text-[12px] text-soft">
        Zeph is an AI companion. It isn’t a mental-health service and can’t help
        in an emergency.
      </p>
    </div>
  );
}
