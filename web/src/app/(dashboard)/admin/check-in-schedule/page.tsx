import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CheckInSchedule } from "@/components/CheckInSchedule";

/**
 * The admin Check-in Schedule page.
 *
 * @returns The page.
 */
export default function AdminCheckInSchedulePage() {
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="Check-in Schedule"
        lead="Everyone who opted in to Check-ins: when each is due, their settings, and why one is held back right now. No content."
      />
      <CheckInSchedule />
    </div>
  );
}
