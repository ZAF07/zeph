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
import { MemoryOffNotice } from "@/components/MemoryOffNotice";
import { PageHero } from "@/components/PageHero";
import { PillLink } from "@/components/PillLink";
import { RecentlyRemembered } from "@/components/RecentlyRemembered";
import { currentTime } from "@/lib/clock";
import { readCopy, type Copy } from "@/lib/copy";
import { greeting, lastTalkedText } from "@/lib/home";
import { memoryOffNote } from "@/lib/memory-off-note";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const cardRow = "flex flex-wrap gap-6";

/**
 * The Dashboard home: a greeting with when the User last talked with Zeph,
 * the Telegram and Check-ins cards, the Memory line, what the User is working
 * toward (the Memory line becomes the "Memory is off" notice while it is
 * off), what Zeph recently remembered, the Plan card (to build) and the AI
 * notice. Every word is Copy.
 *
 * @param props - `copy` is Home's Copy and the Shared Memory-off notes,
 *   read on the server.
 * @returns The page, loading panels, or an error with Try again.
 */
export function DashboardHome({ copy }: { copy: Copy }) {
  const text = (key: string) => readCopy(copy, `home.${key}`);
  const apiClient = useApiClient();
  const homeQuery = useQuery({
    queryKey: queryKeys.home,
    queryFn: () => apiClient.getHome(),
  });

  const now = currentTime();
  const home = homeQuery.data;
  const homeMemoryOffNote = home ? memoryOffNote(copy, home) : null;
  const timeZone = home?.time_zone ?? undefined;

  if (homeQuery.isPending) {
    return (
      <>
        <LoadingPanel shape="banner" label={text("loading")} />
        <LoadingPanel shape="card" label={text("loading_cards")} />
      </>
    );
  }

  if (!home) {
    return (
      <LoadFailed
        title={text("load_failed.title")}
        body={text("load_failed.body")}
        retryLabel={text("load_failed.retry")}
        onRetry={() => void homeQuery.refetch()}
      />
    );
  }

  return (
    <>
      <PageHero
        background="home"
        eyebrow={text("hero.eyebrow")}
        title={greeting(copy, home.name, now, timeZone)}
        body={lastTalkedText(copy, home.last_conversation_at, now, timeZone)}
        actions={
          home.telegram_connection ? (
            <PillLink
              href={home.telegram_chat_url}
              label={text("hero.talk_button")}
              primary
            />
          ) : null
        }
      />
      {home.telegram_connection ? null : (
        <AttentionCard
          title={text("not_connected.title")}
          body={text("not_connected.body")}
          action={
            <PillLink
              href="/connect-telegram"
              label={text("not_connected.button")}
              primary
            />
          }
        />
      )}
      <div className={cardRow}>
        {home.telegram_connection ? (
          <HomeTelegramCard copy={copy} connection={home.telegram_connection} />
        ) : null}
        <HomeCheckInsCard
          copy={copy}
          checkIns={home.check_ins}
          now={now}
          timeZone={timeZone}
        />
      </div>
      {homeMemoryOffNote ? (
        <MemoryOffNotice note={homeMemoryOffNote} canTurnOn={false} />
      ) : (
        <HomeMemoryLine copy={copy} />
      )}
      <div className={`${cardRow} items-start`}>
        <HomeGoals copy={copy} goals={home.goals} timeZone={timeZone} />
        <RecentlyRemembered copy={copy} items={home.recently_remembered} />
      </div>
      <div className={cardRow}>
        <HomePlanCard copy={copy} />
      </div>
      <footer className="flex flex-col gap-1.5 border-t border-line pt-5">
        <p className="m-0 max-w-[620px] text-[14px] text-soft">
          {text("footer.no_streaks")}
        </p>
        <p className="m-0 max-w-[620px] text-[12px] text-soft">
          {text("footer.ai_notice")}
        </p>
      </footer>
    </>
  );
}
