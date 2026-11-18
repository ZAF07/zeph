"use client";

import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { ConversationSummariesList } from "@/components/ConversationSummariesList";
import { LifeThreadsList } from "@/components/LifeThreadsList";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { MemoriesTabs } from "@/components/MemoriesTabs";
import { MemoryItemsList } from "@/components/MemoryItemsList";
import { MemoryOffNotice } from "@/components/MemoryOffNotice";
import { MoveOutcomesList } from "@/components/MoveOutcomesList";
import { PageHero } from "@/components/PageHero";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { SharedPhotosList } from "@/components/SharedPhotosList";
import { Switch } from "@/components/Switch";
import { UserPortraitSection } from "@/components/UserPortraitSection";
import { notAvailableText } from "@/lib/features";
import {
  type MemoriesTab,
  memoriesTabFromQuery,
  searchWithMemoriesTab,
} from "@/lib/memories";
import { queryKeys, useMe, useUpdatePreferences } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Memories page: what Zeph remembers, by Memory Category, its User
 * Portrait of the User, the Life Threads it follows, what helps them (Move
 * Outcomes), the Conversation Summaries and the Shared Photos, each
 * deletable, with the User Memory switch. One tab shows at a time; the
 * address's `?tab=` picks it, and choosing a tab updates `?tab=` without
 * loading the page again.
 *
 * @returns The page, a loading panel, or an error with Try again.
 */
export function Memories() {
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
    queryKey: queryKeys.conversationSummaries,
    queryFn: () => apiClient.listConversationSummaries(),
  });
  const threadsQuery = useQuery({
    queryKey: queryKeys.lifeThreads,
    queryFn: () => apiClient.listLifeThreads(),
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
  const queries = [
    meQuery,
    groupsQuery,
    portraitQuery,
    threadsQuery,
    outcomesQuery,
    summariesQuery,
    photosQuery,
  ];

  const me = meQuery.data;
  const groups = groupsQuery.data;
  const threads = threadsQuery.data;
  const outcomes = outcomesQuery.data;
  const summaries = summariesQuery.data;
  const photos = photosQuery.data;
  const portrait = portraitQuery.data;
  const isLoaded = Boolean(
    me &&
    groups &&
    portrait !== undefined &&
    threads &&
    outcomes &&
    summaries &&
    photos,
  );
  const loadFailed = !isLoaded && queries.some((query) => query.isError);
  const timeZone = me?.time_zone ?? undefined;

  const memoryOn = me?.user_memory_enabled ?? false;
  const memoryUnavailable = me !== undefined && !me.user_memory_available;
  let switchLabel = memoryOn ? "Memory on" : "Memory paused";
  if (memoryUnavailable) {
    switchLabel = notAvailableText;
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
        eyebrow="Memories"
        title="Memories"
        body="What Zeph remembers, what it knows about you, what's going on in your life, what helps you, short summaries of past Conversations and the photos it kept. Delete anything you'd rather it forgot."
        actions={
          me ? (
            <>
              <div className="inline-flex items-center gap-1.5 rounded-pill border border-line bg-panel pr-1 pl-[18px]">
                <span className="text-[14px] font-normal text-text">
                  {switchLabel}
                </span>
                <Switch
                  label="Memory"
                  checked={memoryOn}
                  disabled={updatePreferences.isPending || memoryUnavailable}
                  onChange={changeMemory}
                />
              </div>
              <ChangedInChatCaption
                changedAt={me.changed_in_chat.user_memory}
                timeZone={timeZone}
              />
            </>
          ) : null
        }
      />

      {updatePreferences.isError ? (
        <SaveFailedNote>
          We couldn’t change that. Please try again.
        </SaveFailedNote>
      ) : null}

      {me ? (
        <MemoryOffNotice
          note={me.memory_note}
          canTurnOn={!memoryUnavailable}
          isSaving={updatePreferences.isPending}
          onTurnOn={() => changeMemory(true)}
        />
      ) : null}

      <p className="m-0 text-[13px] text-cream">
        You can also tell Zeph &quot;forget that&quot;.
      </p>

      <MemoriesTabs selected={tab} onSelect={chooseTab} />

      {!isLoaded && !loadFailed ? (
        <LoadingPanel shape="card" label="Loading memories" />
      ) : null}

      {loadFailed ? (
        <LoadFailed
          title="Couldn’t load your memories"
          body="Check your connection and try again. Nothing has been lost."
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
            <MemoryItemsList groups={groups} timeZone={timeZone} />
          ) : null}
          {portrait !== undefined && tab === "about" ? (
            <UserPortraitSection portrait={portrait} timeZone={timeZone} />
          ) : null}
          {threads && tab === "threads" ? (
            <LifeThreadsList threads={threads} timeZone={timeZone} />
          ) : null}
          {outcomes && tab === "helps" ? (
            <MoveOutcomesList outcomes={outcomes} timeZone={timeZone} />
          ) : null}
          {summaries && tab === "summaries" ? (
            <ConversationSummariesList
              summaries={summaries}
              timeZone={timeZone}
            />
          ) : null}
          {photos && tab === "photos" ? (
            <SharedPhotosList photos={photos} timeZone={timeZone} />
          ) : null}
        </div>
      ) : null}
    </>
  );
}
