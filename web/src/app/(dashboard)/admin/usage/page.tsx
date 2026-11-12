import { AdminPageHeader } from "@/components/AdminPageHeader";
import { AdminUsage } from "@/components/AdminUsage";

/**
 * The admin Usage page.
 *
 * @returns The page.
 */
export default function AdminUsagePage() {
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="Usage"
        lead="Tokens, messages and web searches per User per day. Counts only."
      />
      <AdminUsage />
    </div>
  );
}
