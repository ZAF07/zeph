import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PlatformSettingsForm } from "@/components/PlatformSettingsForm";

/**
 * The admin Platform settings page.
 *
 * @returns The page.
 */
export default function AdminSettingsPage() {
  return (
    <>
      <AdminPageHeader
        title="Platform settings"
        lead="Timings and shared wording for every User."
      />
      <PlatformSettingsForm />
    </>
  );
}
