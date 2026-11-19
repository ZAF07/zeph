import { EmptyState } from "@/components/EmptyState";
import { filledPill, outlinedPill } from "@/components/card-styles";
import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInStatusText,
  formatCheckInDay,
  recentCheckInTitle,
} from "@/lib/check-ins";
import { type Copy, readCopy } from "@/lib/copy";

/**
 * The "Recent check-ins" list: each Check-in's Kind, the day it was sent and
 * whether the User replied, or that Zeph gave them space. Never the message,
 * a skip reason or a next time. Ends with how the ignore rule works.
 *
 * @param props - `checkIns` are the recent Check-ins, newest first; `copy`
 *   holds the Check-ins page's Copy; `timeZone` is the User's, to show days
 *   in.
 * @returns The list, or a note that there are none yet.
 */
export function RecentCheckInsList({
  checkIns,
  copy,
  timeZone,
}: {
  checkIns: RecentCheckIn[];
  copy: Copy;
  timeZone?: string;
}) {
  const recentCopy = (slot: string) =>
    readCopy(copy, `check_ins.recent.${slot}`);
  return (
    <section
      aria-labelledby="recent-check-ins-heading"
      className="flex flex-col gap-5 min-[900px]:gap-6"
    >
      <h2
        id="recent-check-ins-heading"
        className="m-0 text-[20px] font-normal text-cream"
      >
        {recentCopy("heading")}
      </h2>
      {checkIns.length === 0 ? (
        <EmptyState
          title={recentCopy("empty_title")}
          body={recentCopy("empty_body")}
        />
      ) : (
        <ul className="m-0 box-border list-none rounded-card border border-line bg-panel px-[22px] py-1.5">
          {checkIns.map((checkIn) => {
            const isReply = checkIn.status === "replied";
            return (
              <li
                key={checkIn.id}
                className="box-content flex min-h-14 flex-wrap items-center justify-between gap-x-4 gap-y-1.5 border-t border-line py-1.5 first:border-t-0"
              >
                <div>
                  <div className="text-[15px] text-text">
                    {recentCheckInTitle(copy, checkIn)}
                  </div>
                  <div className="text-[12px] text-soft">
                    {formatCheckInDay(checkIn.decided_at, timeZone)}
                  </div>
                </div>
                <span className={isReply ? filledPill : outlinedPill}>
                  {checkInStatusText(copy, checkIn.status)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="m-0 text-[13px] text-soft">{recentCopy("ignore_rule")}</p>
    </section>
  );
}
