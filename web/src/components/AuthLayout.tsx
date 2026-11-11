import type { ReactNode } from "react";

import { ZephLogo } from "@/components/ZephLogo";

/**
 * The sign-up and sign-in page frame: a quiet dark panel beside the Clerk form,
 * with the Terms and 18+ lines underneath.
 *
 * @param props - `children` is the Clerk component to show.
 * @returns The page layout.
 */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-wrap">
      <span
        aria-hidden="true"
        className="brand-stripe fixed inset-x-0 top-0 z-10 block h-0.5"
      />
      <aside className="flex min-h-[360px] min-w-0 flex-[1_1_440px] flex-col justify-between gap-12 bg-black px-[clamp(16px,4vw,48px)] py-10 text-subtle">
        <span className="flex items-center gap-2.5 text-subtle">
          <ZephLogo size={28} />
          <span className="text-[26px]">Zeph</span>
        </span>
        <blockquote className="m-0 flex max-w-[30em] flex-col gap-5">
          <p className="m-0 text-[clamp(32px,3.6vw,48px)] leading-[1.12] tracking-[-0.035em]">
            “The unexamined life is not worth living.”
          </p>
          <footer className="text-sm text-on-black-soft">
            Socrates, in Plato’s <cite>Apology</cite>
          </footer>
        </blockquote>
        <p className="m-0 max-w-[34em] text-caption text-on-black-muted">
          Zeph is an AI companion. It isn’t a mental-health service and can’t
          help in an emergency.
        </p>
      </aside>
      <main className="flex min-w-0 flex-[1_1_480px] flex-col items-center justify-center gap-5 px-4 py-12">
        {children}
        <p className="m-0 max-w-[420px] text-center text-caption text-ink-muted">
          By continuing you agree to the <a href="/terms">Terms</a> and{" "}
          <a href="/privacy">Privacy policy</a>. You must be 18 or older to use
          Zeph.
        </p>
      </main>
    </div>
  );
}
