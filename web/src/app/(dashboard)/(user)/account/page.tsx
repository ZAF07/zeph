import type { Metadata } from "next";

import { AccountSettings } from "@/components/AccountSettings";
import { CopyLoadFailed } from "@/components/CopyLoadFailed";
import { PageHeader } from "@/components/PageHeader";
import { pageMetadata, pickCopy, readCopy } from "@/lib/copy";
import { loadCopy } from "@/lib/server-copy";

/**
 * The Account & privacy page's browser tab title and search description,
 * from Copy. When Copy can't be read, the root layout's stay.
 *
 * @returns The page's metadata.
 */
export async function generateMetadata(): Promise<Metadata> {
  const copy = await loadCopy();
  return copy ? pageMetadata(copy, "account") : {};
}

/**
 * The Account & privacy page, where a User changes their profile and
 * User Memory setting, and can delete their data or account. Its words
 * come from Copy, read on the server; only its slots and onboarding's
 * location labels go to the browser.
 *
 * @returns The page, or the couldn't-load block when Copy can't be read.
 */
export default async function AccountPage() {
  const copy = await loadCopy();
  if (!copy) {
    return <CopyLoadFailed />;
  }
  const text = (key: string) => readCopy(copy, `account.header.${key}`);
  return (
    <>
      <PageHeader
        eyebrow={text("eyebrow")}
        title={text("heading")}
        lead={text("lead")}
      />
      <AccountSettings
        copy={pickCopy(copy, ["account.", "onboarding.location."])}
      />
    </>
  );
}
