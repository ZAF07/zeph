"use client";

import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { DaySummariesList } from "@/components/DaySummariesList";
import { KeptQuotesList } from "@/components/KeptQuotesList";
import { LifeThreadsList } from "@/components/LifeThreadsList";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { MemoriesTabs } from "@/components/MemoriesTabs";
import { MemoryItemsList } from "@/components/MemoryItemsList";
import { MemoryOffNotice } from "@/components/MemoryOffNotice";
import { MoveOutcomesList } from "@/components/MoveOutcomesList";
import { PageHero } from "@/components/PageHero";
import { PatternNoticingNotice } from "@/components/PatternNoticingNotice";
import { PatternsList } from "@/components/PatternsList";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { SharedPhotosList } from "@/components/SharedPhotosList";
import { Switch } from "@/components/Switch";
import { UserPortraitSection } from "@/components/UserPortraitSection";
import { type Copy, readCopy } from "@/lib/copy";
import {
  type MemoriesTab,
  memoriesTabFromQuery,
  searchWithMemoriesTab,
} from "@/lib/memories";
import { memoryOffNote } from "@/lib/memory-off-note";
import { queryKeys, useMe, useUpdatePreferences } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Memories page: what Zeph remembers, by Memory Category, its User
 * Portrait of the User, the Life Threads it follows, the Patterns they
 * agreed with, what helps them (Move Outcomes), the Day Summaries, the
 * Shared Photos and the quotes Zeph keeps as evidence, each deletable, with
 * the User Memory switch and, until they press Got it, the notice saying
 * Zeph now keeps some of their words. One tab shows at a time; the
 * address's `?tab=` picks it, and choosing a tab updates `?tab=` without
 * loading the page again. Every word is the Memories tab's Copy.
 *
 * @param props - `copy` holds the Memories page's Copy slots and the
 *   Shared Memory-off notes.
 * @returns The page, a loading panel, or an error with Try again.
 */
export function Memories({ copy }: { copy: Copy }) {
  const memoriesCopy = (slot: string) => readCopy(copy, `memories.${slot}`);
  const apiClient = useApiClient();
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<MemoriesTab>(() =>
    memoriesTabFromQuery(searchParams.get("tab")),
  );
  const updatePreferences = useUpdatePreferences();
  const meQuery = useMe();
  const groupsQuery = useQuery({
    queryKey: queryKeys.memoryGroups,
    queryFn: () => apiClient.listMemoryGroups(),
  });
  const summariesQuery = useQuery({
    queryKey: queryKeys.daySummaries,
    queryFn: () => apiClient.listDaySummaries(),
  });
  const threadsQuery = useQuery({
    queryKey: queryKeys.lifeThreads,
    queryFn: () => apiClient.listLifeThreads(),
  });
  const patternsQuery = useQuery({
    queryKey: queryKeys.patterns,
    queryFn: () => apiClient.listPatterns(),
  });
  const outcomesQuery = useQuery({
    queryKey: queryKeys.moveOutcomes,
    queryFn: () => apiClient.listMoveOutcomes(),
  });
  const portraitQuery = useQuery({
    queryKey: queryKeys.userPortrait,
    queryFn: () => apiClient.getUserPortrait(),
  });
  const photosQuery = useQuery({
    queryKey: queryKeys.sharedPhotos,
    queryFn: () => apiClient.listSharedPhotos(),
  });
  const quotesQuery = useQuery({
    queryKey: queryKeys.keptQuotes,
    queryFn: () => apiClient.listKeptQuotes(),
  });
  const queries = [
    meQuery,
    groupsQuery,
    portraitQuery,
    threadsQuery,
    patternsQuery,
    outcomesQuery,
    summariesQuery,
    photosQuery,
    quotesQuery,
  ];

  const me = meQuery.data;
  const groups = groupsQuery.data;
  const threads = threadsQuery.data;
  const patterns = patternsQuery.data;
  const outcomes = outcomesQuery.data;
  const summaries = summariesQuery.data;
  const photos = photosQuery.data;
  const quotes = quotesQuery.data;
  const portrait = portraitQuery.data;
  const isLoaded = Boolean(
    me &&
    groups &&
    portrait !== undefined &&
    threads &&
    patterns &&
    outcomes &&
    summaries &&
    photos &&
    quotes,
  );
  const loadFailed = !isLoaded && queries.some((query) => query.isError);
  const timeZone = me?.time_zone ?? undefined;

  const memoryOn = me?.user_memory_enabled ?? false;
  const memoryUnavailable = me !== undefined && !me.user_memory_available;
  let switchLabel = memoriesCopy(memoryOn ? "switch.on" : "switch.paused");
  if (memoryUnavailable) {
    switchLabel = memoriesCopy("switch.not_available");
  }

  function changeMemory(enabled: boolean) {
    updatePreferences.mutate({ user_memory_enabled: enabled });
  }

  function chooseTab(next: MemoriesTab) {
    setTab(next);
    const search = searchWithMemoriesTab(window.location.search, next);
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${search}`,
    );
  }

  return (
    <>
      <PageHero
        background="memories"
        eyebrow={memoriesCopy("hero.eyebrow")}
        title={memoriesCopy("hero.heading")}
        body={memoriesCopy("hero.lead")}
        actions={
          me ? (
            <>
              <div className="inline-flex items-center gap-1.5 rounded-pill border border-line bg-panel pr-1 pl-[18px]">
                <span className="text-[14px] font-normal text-text">
                  {switchLabel}
                </span>
                <Switch
                  label={memoriesCopy("switch.label")}
                  checked={memoryOn}
                  disabled={updatePreferences.isPending || memoryUnavailable}
                  onChange={changeMemory}
                />
              </div>
              <ChangedInChatCaption
                changedAt={me.changed_in_chat.user_memory}
                timeZone={timeZone}
                text={memoriesCopy("switch.changed_in_chat")}
              />
            </>
          ) : null
        }
      />

      {updatePreferences.isError ? (
        <SaveFailedNote>{memoriesCopy("switch.save_failed")}</SaveFailedNote>
      ) : null}

      {me ? <PatternNoticingNotice me={me} copy={copy} /> : null}

      {me ? (
        <MemoryOffNotice
          note={memoryOffNote(copy, me)}
          canTurnOn={!memoryUnavailable}
          isSaving={updatePreferences.isPending}
          onTurnOn={() => changeMemory(true)}
          turnOnLabel={memoriesCopy("memory_off.turn_on")}
        />
      ) : null}

      <p className="m-0 text-[13px] text-cream">
        {memoriesCopy("forget_that")}
      </p>

      <MemoriesTabs copy={copy} selected={tab} onSelect={chooseTab} />

      {!isLoaded && !loadFailed ? (
        <LoadingPanel shape="card" label={memoriesCopy("loading")} />
      ) : null}

      {loadFailed ? (
        <LoadFailed
          title={memoriesCopy("load_failed.title")}
          body={memoriesCopy("load_failed.body")}
          retryLabel={memoriesCopy("load_failed.retry")}
          onRetry={() => {
            for (const query of queries) {
              void query.refetch();
            }
          }}
        />
      ) : null}

      {isLoaded ? (
        <div role="tabpanel" className="flex flex-col gap-6">
          {groups && tab === "memories" ? (
            <MemoryItemsList groups={groups} copy={copy} timeZone={timeZone} />
          ) : null}
          {portrait !== undefined && tab === "about" ? (
            <UserPortraitSection
              portrait={portrait}
              copy={copy}
              timeZone={timeZone}
            />
          ) : null}
          {threads && tab === "threads" ? (
            <LifeThreadsList
              threads={threads}
              copy={copy}
              timeZone={timeZone}
            />
          ) : null}
          {patterns && tab === "patterns" ? (
            <PatternsList patterns={patterns} copy={copy} timeZone={timeZone} />
          ) : null}
          {outcomes && tab === "helps" ? (
            <MoveOutcomesList
              outcomes={outcomes}
              copy={copy}
              timeZone={timeZone}
            />
          ) : null}
          {summaries && tab === "summaries" ? (
            <DaySummariesList summaries={summaries} copy={copy} />
          ) : null}
          {photos && tab === "photos" ? (
            <SharedPhotosList photos={photos} copy={copy} timeZone={timeZone} />
          ) : null}
          {quotes && tab === "quotes" ? (
            <KeptQuotesList quotes={quotes} copy={copy} />
          ) : null}
        </div>
      ) : null}
    </>
  );
}
