import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CheckInLog } from "@/components/CheckInLog";

/**
 * The admin Check-in log page.
 *
 * @returns The page.
 */
export default function AdminCheckInLogPage() {
  return (
    <>
      <AdminPageHeader
        title="Check-in log"
        lead="Every check-in Zeph sent or chose to skip, newest first. You see the kind or the skip reason for each user, never the message text."
      />
      <CheckInLog />
    </>
  );
}
