import Link from "next/link";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { DetailRow } from "@/components/DetailRow";
import { HomeCard } from "@/components/HomeCard";
import { cardLink, filledPill, outlinedPill } from "@/components/card-styles";
import type { HomeCheckIns } from "@/lib/api-client";
import { readCopy, type Copy } from "@/lib/copy";
import {
  checkInFrequencyText,
  homePauseEndText,
  lastCheckInText,
  quietHoursText,
} from "@/lib/home";

/**
 * The Dashboard home card for Check-ins: on, paused until a day, off, or
 * not available on the User's account, with how often, quiet hours and the
 * last Check-in sent. Never a next time.
 *
 * @param props - `copy` is Home's Copy, `checkIns` the User's Check-in
 *   status, `now` the current moment and `timeZone` the User's, to name
 *   days in.
 * @returns The card.
 */
export function HomeCheckInsCard({
  copy,
  checkIns,
  now,
  timeZone,
}: {
  copy: Copy;
  checkIns: HomeCheckIns;
  now: Date;
  timeZone?: string;
}) {
  const text = (key: string) => readCopy(copy, `home.check_ins.${key}`);
  const isWorking = checkIns.available && checkIns.enabled;
  let pill = <span className={filledPill}>{text("on")}</span>;
  if (!isWorking) {
    pill = <span className={outlinedPill}>{text("off")}</span>;
  } else if (checkIns.paused) {
    pill = <span className={outlinedPill}>{text("paused")}</span>;
  }

  return (
    <HomeCard
      headingId="home-check-ins-heading"
      title={text("title")}
      aside={pill}
      caption={text("caption")}
      basis="narrow"
    >
      {!checkIns.available ? (
        <DetailRow label={text("status_label")}>
          {text("not_available")}
        </DetailRow>
      ) : !checkIns.enabled ? (
        <DetailRow label={text("status_label")}>{text("turned_off")}</DetailRow>
      ) : (
        <>
          {checkIns.paused ? (
            <DetailRow label={text("paused_label")}>
              {homePauseEndText(copy, checkIns.paused_until, timeZone)}
              <ChangedInChatCaption
                changedAt={checkIns.pause_changed_in_chat_at ?? undefined}
                timeZone={timeZone}
                text={text("changed_in_chat")}
              />
            </DetailRow>
          ) : (
            <DetailRow label={text("frequency_label")}>
              {checkInFrequencyText(copy, checkIns.frequency)}
            </DetailRow>
          )}
          <DetailRow label={text("quiet_hours_label")}>
            {quietHoursText(
              copy,
              checkIns.quiet_hours_start,
              checkIns.quiet_hours_end,
            )}
          </DetailRow>
          <DetailRow label={text("last_label")}>
            {lastCheckInText(copy, checkIns.last_sent, now, timeZone)}
          </DetailRow>
        </>
      )}
      <div className="border-t border-line">
        <Link href="/check-ins" className={cardLink}>
          {text("settings_link")}
        </Link>
      </div>
    </HomeCard>
  );
}
