import { AccountSettings } from "@/components/AccountSettings";

/**
 * The Account & privacy page, where a User changes their profile and
 * User Memory setting at any time.
 *
 * @returns The page.
 */
export default function AccountPage() {
  return (
    <>
      <header className="flex flex-col gap-2">
        <h1 className="m-0 text-h1 font-normal">Account &amp; privacy</h1>
        <p className="m-0 max-w-[40em] text-body text-ink-soft">
          Everything about you, and everything you’ve shared, is yours to change
          or take back.
        </p>
      </header>
      <AccountSettings />
    </>
  );
}
