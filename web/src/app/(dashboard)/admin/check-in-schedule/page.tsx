import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CheckInSchedule } from "@/components/CheckInSchedule";

/**
 * The admin Check-in Schedule page. `?search=` fills the search box, so the
 * Users page can open one User here.
 *
 * @param props - `searchParams` holds the address's query.
 * @returns The page.
 */
export default async function AdminCheckInSchedulePage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string | string[] }>;
}) {
  const { search } = await searchParams;
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="Check-in Schedule"
        lead="Everyone who opted in to Check-ins: when each is due, their settings, and why one is held back right now. No content."
      />
      <CheckInSchedule
        initialSearch={typeof search === "string" ? search : ""}
      />
    </div>
  );
}
