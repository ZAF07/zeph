import Link from "next/link";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { DetailRow } from "@/components/DetailRow";
import { HomeCard } from "@/components/HomeCard";
import { cardLink, filledPill, outlinedPill } from "@/components/card-styles";
import type { HomeCheckIns } from "@/lib/api-client";
import { pauseEndText } from "@/lib/check-ins";
import { notAvailableText } from "@/lib/features";
import {
  checkInFrequencyText,
  lastCheckInText,
  quietHoursText,
} from "@/lib/home";

/**
 * The Dashboard home card for Check-ins: on, paused until a day, off, or
 * not available on the User's account, with how often, quiet hours and the
 * last Check-in sent. Never a next time.
 *
 * @param props - `checkIns` is the User's Check-in status, `now` the current
 *   moment and `timeZone` the User's, to name days in.
 * @returns The card.
 */
export function HomeCheckInsCard({
  checkIns,
  now,
  timeZone,
}: {
  checkIns: HomeCheckIns;
  now: Date;
  timeZone?: string;
}) {
  const isWorking = checkIns.available && checkIns.enabled;
  let pill = <span className={filledPill}>On</span>;
  if (!isWorking) {
    pill = <span className={outlinedPill}>Off</span>;
  } else if (checkIns.paused) {
    pill = <span className={outlinedPill}>Paused</span>;
  }

  return (
    <HomeCard
      headingId="home-check-ins-heading"
      title="Check-ins"
      aside={pill}
      caption="Zeph chooses the moment. There is no fixed schedule."
      basis="narrow"
    >
      {!checkIns.available ? (
        <DetailRow label="Status">{notAvailableText}</DetailRow>
      ) : !checkIns.enabled ? (
        <DetailRow label="Status">Zeph only replies when you message</DetailRow>
      ) : (
        <>
          {checkIns.paused ? (
            <DetailRow label="Paused">
              {pauseEndText(checkIns.paused_until, timeZone)}
              <ChangedInChatCaption
                changedAt={checkIns.pause_changed_in_chat_at ?? undefined}
                timeZone={timeZone}
              />
            </DetailRow>
          ) : (
            <DetailRow label="How often">
              {checkInFrequencyText(checkIns.frequency)}
            </DetailRow>
          )}
          <DetailRow label="Quiet hours">
            {quietHoursText(
              checkIns.quiet_hours_start,
              checkIns.quiet_hours_end,
            )}
          </DetailRow>
          <DetailRow label="Last check-in">
            {lastCheckInText(checkIns.last_sent, now, timeZone)}
          </DetailRow>
        </>
      )}
      <div className="border-t border-line">
        <Link href="/check-ins" className={cardLink}>
          Change check-in settings
        </Link>
      </div>
    </HomeCard>
  );
}
