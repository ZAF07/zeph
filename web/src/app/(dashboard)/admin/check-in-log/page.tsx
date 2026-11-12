import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CheckInLog } from "@/components/CheckInLog";

/**
 * The admin Check-in log page.
 *
 * @returns The page.
 */
export default function AdminCheckInLogPage() {
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="Check-in log"
        lead="Every decision the Check-ins service made: sent, or skipped and why. No content."
      />
      <CheckInLog />
    </div>
  );
}
