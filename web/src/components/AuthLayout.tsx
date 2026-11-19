import Link from "next/link";
import { Fragment, type ReactNode } from "react";

import { secondaryButton } from "@/components/button-styles";
import { PublicHeader } from "@/components/PublicHeader";
import { type Copy, fillPlaceholderParts, readCopy } from "@/lib/copy";

/** Which auth page the frame is around: sign-in or sign-up. */
export type AuthPage = "sign_in" | "sign_up";

const otherPageHref: Record<AuthPage, string> = {
  sign_in: "/sign-up",
  sign_up: "/sign-in",
};

/**
 * The sign-in and sign-up page frame, from the design's `Login` and `Signup`
 * files: the archway picture behind the public header, a card holding the
 * eyebrow and the Clerk form, and the Terms, 18+ and AI companion lines.
 * The card carries `data-clerk-card`, which the pixel test masks. Every
 * word around the Clerk form is Copy; the form's own text is set in Clerk.
 *
 * @param props - `copy` is the website's Copy; `page` says which auth page
 *   this is, which picks its eyebrow and the other page offered in the
 *   header; `children` is the Clerk component.
 * @returns The page layout.
 */
export function AuthLayout({
  copy,
  page,
  children,
}: {
  copy: Copy;
  page: AuthPage;
  children: ReactNode;
}) {
  const termsLine = fillPlaceholderParts(readCopy(copy, "auth.terms_line"), {
    terms: <a href="/terms">{readCopy(copy, "auth.terms_link")}</a>,
    privacy: <a href="/privacy">{readCopy(copy, "auth.privacy_link")}</a>,
  });
  return (
    <div className="flex min-h-[800px] flex-col [background:linear-gradient(180deg,rgba(10,32,44,.25),rgba(10,32,44,.25)),url(/design/auth-archway.jpg)_left_bottom/cover_no-repeat_#0A202C] max-[899px]:min-h-[920px] max-[899px]:[background:linear-gradient(180deg,#0A202C_0%,#0A202C_calc(100%_-_390px),rgba(10,32,44,0)_calc(100%_-_260px)),url(/design/auth-archway.jpg)_left_bottom/auto_390px_no-repeat_#0A202C]">
      <PublicHeader
        wordmark={readCopy(copy, "shared.wordmark")}
        homeLinkLabel={readCopy(copy, "shared.header.home_link_label")}
        actions={
          <>
            <span className="text-soft max-[899px]:hidden">
              {readCopy(copy, `auth.${page}.header_prompt`)}
            </span>
            <Link href={otherPageHref[page]} className={secondaryButton}>
              {readCopy(copy, `auth.${page}.header_link`)}
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
              {readCopy(copy, `auth.${page}.eyebrow`)}
            </div>
            {children}
          </div>
          <p className="m-0 text-center text-[12px] text-soft">
            {termsLine.map((piece, index) => (
              <Fragment key={index}>{piece}</Fragment>
            ))}
          </p>
        </div>
      </main>
      <p className="m-0 px-8 pb-6 text-center text-[12px] text-soft">
        {readCopy(copy, "auth.ai_line")}
      </p>
    </div>
  );
}
