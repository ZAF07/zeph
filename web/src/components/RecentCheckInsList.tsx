import { EmptyState } from "@/components/EmptyState";
import { filledPill, outlinedPill } from "@/components/card-styles";
import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInStatusLabels,
  formatCheckInDay,
  recentCheckInTitle,
} from "@/lib/check-ins";

/**
 * The "Recent check-ins" list: each Check-in's Kind, the day it was sent and
 * whether the User replied, or that Zeph gave them space. Never the message,
 * a skip reason or a next time. Ends with how the ignore rule works.
 *
 * @param props - `checkIns` are the recent Check-ins, newest first;
 *   `timeZone` is the User's, to show days in.
 * @returns The list, or a note that there are none yet.
 */
export function RecentCheckInsList({
  checkIns,
  timeZone,
}: {
  checkIns: RecentCheckIn[];
  timeZone?: string;
}) {
  return (
    <section
      aria-labelledby="recent-check-ins-heading"
      className="flex flex-col gap-5 min-[900px]:gap-6"
    >
      <h2
        id="recent-check-ins-heading"
        className="m-0 text-[20px] font-normal text-cream"
      >
        Recent check-ins
      </h2>
      {checkIns.length === 0 ? (
        <EmptyState
          title="No check-ins yet"
          body="When Zeph checks in, you’ll see it here with whether you replied."
        />
      ) : (
        <ul className="m-0 box-border list-none rounded-card border border-line bg-panel px-[22px] py-1.5">
          {checkIns.map((checkIn) => {
            const status = checkInStatusLabels[checkIn.status];
            return (
              <li
                key={checkIn.id}
                className="box-content flex min-h-14 flex-wrap items-center justify-between gap-x-4 gap-y-1.5 border-t border-line py-1.5 first:border-t-0"
              >
                <div>
                  <div className="text-[15px] text-text">
                    {recentCheckInTitle(checkIn)}
                  </div>
                  <div className="text-[12px] text-soft">
                    {formatCheckInDay(checkIn.decided_at, timeZone)}
                  </div>
                </div>
                <span className={status.isFilled ? filledPill : outlinedPill}>
                  {status.label}
                </span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="m-0 text-[13px] text-soft">
        If a few go unanswered, Zeph will pause and ask once if you&apos;d like
        fewer.
      </p>
    </section>
  );
}
