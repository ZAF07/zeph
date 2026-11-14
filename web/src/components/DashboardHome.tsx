"use client";

import { useCallback, useEffect, useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { ConnectTelegramBanner } from "@/components/ConnectTelegramBanner";
import { HomeCheckInsCard } from "@/components/HomeCheckInsCard";
import { HomeGoals } from "@/components/HomeGoals";
import { HomeTelegramCard } from "@/components/HomeTelegramCard";
import { LoadFailed } from "@/components/LoadFailed";
import { MemoryNote } from "@/components/MemoryNote";
import { RecentlyRemembered } from "@/components/RecentlyRemembered";
import type { Home } from "@/lib/api-client";
import { greeting, todayHeading } from "@/lib/home";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  { kind: "loading" } | { kind: "failed" } | { kind: "loaded"; home: Home };

const twoColumns =
  "grid grid-cols-[repeat(auto-fit,minmax(min(320px,100%),1fr))] gap-6";

/**
 * The Dashboard home: a greeting, the Telegram and Check-ins cards, what the
 * User is working toward, what Zeph recently remembered, and the AI notice.
 *
 * @returns The page, a loading block, or an error with Try again.
 */
export function DashboardHome() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({ kind: "loaded", home: await apiClient.getHome() });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  const now = new Date();
  const home = state.kind === "loaded" ? state.home : null;
  const timeZone = home?.time_zone ?? undefined;

  return (
    <>
      <header className="flex flex-wrap items-end justify-between gap-6">
        <div className="flex flex-col gap-2">
          <p className="m-0 text-sm text-ink-muted">
            {todayHeading(now, timeZone)}
          </p>
          <h1 className="m-0 text-h1 font-normal">
            {greeting(home?.name ?? null, now, timeZone)}
          </h1>
        </div>
        {home?.telegram_connection ? (
          <a href={home.telegram_chat_url} className={primaryButton}>
            Talk to Zeph
          </a>
        ) : null}
      </header>

      {state.kind === "loading" ? (
        <div
          aria-busy="true"
          aria-label="Loading your Dashboard"
          className="flex flex-col gap-6"
        >
          <div className={twoColumns}>
            <span className="block h-[180px] rounded-card bg-subtle" />
            <span className="block h-[180px] rounded-card bg-subtle" />
          </div>
          <span className="block h-7 w-[320px] max-w-[80%] rounded bg-subtle" />
          <span className="block h-[200px] rounded-card bg-subtle" />
        </div>
      ) : null}

      {state.kind === "failed" ? (
        <LoadFailed
          title="We couldn’t load your Dashboard"
          body="Something went wrong on our side. Zeph is still reachable in Telegram, and nothing you’ve shared is lost."
          onRetry={() => void load()}
        />
      ) : null}

      {home ? (
        <>
          {home.telegram_connection ? null : <ConnectTelegramBanner />}
          <div className={twoColumns}>
            {home.telegram_connection ? (
              <HomeTelegramCard
                connection={home.telegram_connection}
                lastConversationAt={home.last_conversation_at}
                now={now}
                timeZone={timeZone}
              />
            ) : null}
            <HomeCheckInsCard checkIns={home.check_ins} timeZone={timeZone} />
          </div>
          <MemoryNote note={home.memory_note} />
          <HomeGoals goals={home.goals} timeZone={timeZone} />
          <RecentlyRemembered
            items={home.recently_remembered}
            timeZone={timeZone}
          />
          <footer className="flex flex-col gap-1.5 border-t border-line pt-5">
            <p className="m-0 max-w-[42em] text-sm text-ink-muted">
              Zeph doesn’t count streaks or time spent. If you go quiet for a
              while, that’s fine — it’ll be here when you’re ready.
            </p>
            <p className="m-0 text-caption text-ink-muted">{home.ai_notice}</p>
          </footer>
        </>
      ) : null}
    </>
  );
}
