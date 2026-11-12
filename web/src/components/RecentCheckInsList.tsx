import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInStatusLabels,
  formatCheckInDay,
  formatCheckInSentAt,
  recentCheckInTitle,
} from "@/lib/check-ins";

/**
 * The "Recent check-ins" list: each Check-in's Kind, when it was sent and
 * whether the User replied, or that Zeph skipped it to give them space.
 * Never the message, a skip reason or a next time. Ends with how the
 * ignore rule works.
 *
 * @param props - `checkIns` are the recent Check-ins, newest first;
 *   `timeZone` is the User's, to show times in.
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
      className="flex flex-col gap-4"
    >
      <h2 id="recent-check-ins-heading" className="m-0 text-[28px] font-normal">
        Recent check-ins
      </h2>
      {checkIns.length === 0 ? (
        <div className="flex flex-col gap-1 rounded-card border border-dashed border-line-strong px-6 py-8 text-center">
          <span className="text-h3">No Check-ins yet</span>
          <p className="m-0 text-caption text-ink-muted">
            When Zeph reaches out, or chooses to give you space, it’ll show
            here.
          </p>
        </div>
      ) : (
        <ul className="m-0 list-none rounded-card border border-line bg-white p-0">
          {checkIns.map((checkIn, index) => {
            const status = checkInStatusLabels[checkIn.status];
            const isSkipped = checkIn.outcome === "skipped";
            return (
              <li
                key={checkIn.id}
                className={`flex flex-wrap items-center justify-between gap-3 px-6 py-4 ${
                  index === 0 ? "" : "border-t border-line"
                }`}
              >
                <span className="flex min-w-0 flex-col gap-0.5">
                  <span
                    className={`font-medium ${isSkipped ? "text-ink-soft" : ""}`}
                  >
                    {recentCheckInTitle(checkIn)}
                  </span>
                  <span className="text-caption text-ink-muted">
                    {isSkipped
                      ? formatCheckInDay(checkIn.decided_at, timeZone)
                      : formatCheckInSentAt(checkIn.decided_at, timeZone)}
                  </span>
                </span>
                <span
                  className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium ${status.pill}`}
                >
                  {status.label}
                </span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="m-0 text-sm text-ink-muted">
        If a few go unanswered, Zeph will pause and ask once if you’d like
        fewer.
      </p>
    </section>
  );
}
