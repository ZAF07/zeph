"use client";

import { useQuery } from "@tanstack/react-query";

import { AttentionCard } from "@/components/AttentionCard";
import { HomeCheckInsCard } from "@/components/HomeCheckInsCard";
import { HomeGoals } from "@/components/HomeGoals";
import { HomeMemoryLine } from "@/components/HomeMemoryLine";
import { HomePlanCard } from "@/components/HomePlanCard";
import { HomeTelegramCard } from "@/components/HomeTelegramCard";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { PageHero } from "@/components/PageHero";
import { PillLink } from "@/components/PillLink";
import { RecentlyRemembered } from "@/components/RecentlyRemembered";
import { currentTime } from "@/lib/clock";
import { greeting, lastTalkedText } from "@/lib/home";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const cardRow = "flex flex-wrap gap-6";

/**
 * The Dashboard home: a greeting with when the User last talked with Zeph,
 * the Telegram and Check-ins cards, the Memory line, what the User is working
 * toward, what Zeph recently remembered, the Plan card (to build) and the AI
 * notice.
 *
 * @returns The page, loading panels, or an error with Try again.
 */
export function DashboardHome() {
  const apiClient = useApiClient();
  const homeQuery = useQuery({
    queryKey: queryKeys.home,
    queryFn: () => apiClient.getHome(),
  });

  const now = currentTime();
  const home = homeQuery.data;
  const timeZone = home?.time_zone ?? undefined;

  if (homeQuery.isPending) {
    return (
      <>
        <LoadingPanel shape="banner" label="Loading your Dashboard" />
        <LoadingPanel shape="card" label="Loading your cards" />
      </>
    );
  }

  if (!home) {
    return (
      <LoadFailed
        title="We couldn’t load your Dashboard"
        body="Something went wrong on our side. Zeph is still reachable in Telegram, and nothing you’ve shared is lost."
        onRetry={() => void homeQuery.refetch()}
      />
    );
  }

  return (
    <>
      <PageHero
        background="home"
        eyebrow="Home"
        title={greeting(home.name, now, timeZone)}
        body={lastTalkedText(home.last_conversation_at, now, timeZone)}
        actions={
          home.telegram_connection ? (
            <PillLink
              href={home.telegram_chat_url}
              label="Talk to Zeph"
              primary
            />
          ) : null
        }
      />
      {home.telegram_connection ? null : (
        <AttentionCard
          title="Zeph can’t reach you yet."
          body="Conversations and check-ins happen in Telegram. Linking takes one tap."
          action={
            <PillLink
              href="/connect-telegram"
              label="Connect Telegram"
              primary
            />
          }
        />
      )}
      <div className={cardRow}>
        {home.telegram_connection ? (
          <HomeTelegramCard connection={home.telegram_connection} />
        ) : null}
        <HomeCheckInsCard
          checkIns={home.check_ins}
          now={now}
          timeZone={timeZone}
        />
      </div>
      <HomeMemoryLine note={home.memory_note} />
      <div className={`${cardRow} items-start`}>
        <HomeGoals goals={home.goals} timeZone={timeZone} />
        <RecentlyRemembered items={home.recently_remembered} />
      </div>
      <div className={cardRow}>
        <HomePlanCard />
      </div>
      <footer className="flex flex-col gap-1.5 border-t border-line pt-5">
        <p className="m-0 max-w-[620px] text-[14px] text-soft">
          Zeph doesn&apos;t count streaks or time spent. If you go quiet for a
          while, that&apos;s fine. It&apos;ll be here when you&apos;re ready.
        </p>
        <p className="m-0 max-w-[620px] text-[12px] text-soft">
          {home.ai_notice}
        </p>
      </footer>
    </>
  );
}
