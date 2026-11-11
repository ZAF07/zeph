import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PlatformSettingsForm } from "@/components/PlatformSettingsForm";

/**
 * The admin Platform settings page.
 *
 * @returns The page.
 */
export default function AdminSettingsPage() {
  return (
    <div className="flex max-w-[920px] flex-col gap-[30px]">
      <AdminPageHeader
        title="Platform settings"
        lead="Timings and shared wording for every User."
      />
      <PlatformSettingsForm />
    </div>
  );
}
