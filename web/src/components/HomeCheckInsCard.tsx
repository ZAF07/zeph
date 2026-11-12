import Link from "next/link";

import type { HomeCheckIns } from "@/lib/api-client";
import { pauseEndText } from "@/lib/check-ins";
import {
  checkInFrequencyText,
  lastCheckInText,
  quietHoursText,
} from "@/lib/home";

const statusLine = "m-0 flex items-center gap-2.5 text-[17px] font-medium";
const pill =
  "inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium";

/**
 * The Dashboard home card for Check-ins: on, paused until a day, or off,
 * and the last Check-in sent. Never a next time.
 *
 * @param props - `checkIns` is the User's Check-in status; `timeZone` is
 *   theirs, to show days in.
 * @returns The card.
 */
export function HomeCheckInsCard({
  checkIns,
  timeZone,
}: {
  checkIns: HomeCheckIns;
  timeZone?: string;
}) {
  return (
    <section
      aria-labelledby="home-check-ins-heading"
      className="flex flex-col gap-3 rounded-card border border-line bg-white p-7"
    >
      <h2
        id="home-check-ins-heading"
        className="m-0 font-mono text-eyebrow font-semibold uppercase text-ink-muted"
      >
        Check-ins
      </h2>
      {!checkIns.enabled ? (
        <p className={statusLine}>
          <span className={`${pill} bg-code text-ink-body`}>Off</span>
          Zeph only replies when you message
        </p>
      ) : checkIns.paused ? (
        <p className={statusLine}>
          <span className={`${pill} bg-yellow-tint text-yellow-deep`}>
            Paused
          </span>
          {pauseEndText(checkIns.paused_until, timeZone)}
        </p>
      ) : (
        <div className="flex flex-col gap-1.5">
          <p className={statusLine}>
            <span className={`${pill} bg-blue-tint text-blue-deep`}>On</span>
            {checkInFrequencyText(checkIns.frequency)}
          </p>
          <p className="m-0 text-caption text-ink-muted">
            {quietHoursText(
              checkIns.quiet_hours_start,
              checkIns.quiet_hours_end,
            )}
          </p>
        </div>
      )}
      {checkIns.enabled ? (
        <p className="m-0 border-t border-line pt-3 text-[15px] text-ink-soft">
          {lastCheckInText(checkIns.last_sent, timeZone)}
        </p>
      ) : null}
      <Link
        href="/check-ins"
        className="inline-flex min-h-11 items-center self-start text-sm"
      >
        Check-in settings
      </Link>
    </section>
  );
}
