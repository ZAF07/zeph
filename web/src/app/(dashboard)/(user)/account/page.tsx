import { AccountSettings } from "@/components/AccountSettings";
import { PageHeader } from "@/components/PageHeader";

/**
 * The Account & privacy page, where a User changes their profile and
 * User Memory setting, and can delete their data or account.
 *
 * @returns The page.
 */
export default function AccountPage() {
  return (
    <>
      <PageHeader
        eyebrow="Account & privacy"
        title="Account & privacy"
        lead="Your details, what Zeph is allowed to keep, and how to remove it."
      />
      <AccountSettings />
    </>
  );
}
