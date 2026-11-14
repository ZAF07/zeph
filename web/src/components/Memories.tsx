"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { ConversationSummariesList } from "@/components/ConversationSummariesList";
import { LoadFailed } from "@/components/LoadFailed";
import { MemoryNote } from "@/components/MemoryNote";
import { MemoryItemsList } from "@/components/MemoryItemsList";
import { SharedPhotosList } from "@/components/SharedPhotosList";
import { Switch } from "@/components/Switch";
import { notAvailableText } from "@/lib/features";
import { queryKeys, useMe, useUpdatePreferences } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type Tab = "memories" | "summaries" | "photos";

const tabs: { id: Tab; label: string }[] = [
  { id: "memories", label: "Memories" },
  { id: "summaries", label: "Conversation Summaries" },
  { id: "photos", label: "Photos" },
];

/**
 * The Memories page: what Zeph remembers, by Memory Category, the
 * Conversation Summaries and the Shared Photos, each deletable, with the
 * User Memory switch.
 *
 * @returns The page, a loading block, or an error with Try again.
 */
export function Memories() {
  const apiClient = useApiClient();
  const [tab, setTab] = useState<Tab>("memories");
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
  const photosQuery = useQuery({
    queryKey: queryKeys.sharedPhotos,
    queryFn: () => apiClient.listSharedPhotos(),
  });
  const queries = [meQuery, groupsQuery, summariesQuery, photosQuery];

  const me = meQuery.data;
  const groups = groupsQuery.data;
  const summaries = summariesQuery.data;
  const photos = photosQuery.data;
  const isLoaded = Boolean(me && groups && summaries && photos);
  const loadFailed = !isLoaded && queries.some((query) => query.isError);
  const timeZone = me?.time_zone ?? undefined;

  const memoryOn = me?.user_memory_enabled ?? false;
  const memoryUnavailable = me !== undefined && !me.user_memory_available;
  let switchLabel = memoryOn ? "Memory on" : "Memory paused";
  if (memoryUnavailable) {
    switchLabel = notAvailableText;
  }

  return (
    <>
      <header className="flex flex-wrap items-start justify-between gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="m-0 text-h1 font-normal">Memories</h1>
          <p className="m-0 max-w-[40em] text-body text-ink-soft">
            What Zeph remembers, short summaries of past Conversations and the
            photos it kept. Delete anything you’d rather it forgot.
          </p>
          <p className="m-0 text-caption text-blue">
            You can also tell Zeph “forget that”.
          </p>
        </div>
        {me ? (
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-3 rounded-full border border-line bg-white py-1.5 pr-1.5 pl-[18px]">
              <span className="text-sm font-medium">{switchLabel}</span>
              <Switch
                label="Memory"
                checked={memoryOn}
                disabled={updatePreferences.isPending || memoryUnavailable}
                onChange={(next) =>
                  updatePreferences.mutate({ user_memory_enabled: next })
                }
              />
            </div>
            <ChangedInChatCaption
              changedAt={me.changed_in_chat.user_memory}
              timeZone={timeZone}
            />
            {updatePreferences.isError ? (
              <p role="alert" className="m-0 text-sm text-danger-deep">
                We couldn’t change that. Please try again.
              </p>
            ) : null}
          </div>
        ) : null}
      </header>

      {me ? <MemoryNote note={me.memory_note} /> : null}

      <div
        role="tablist"
        aria-label="Memories"
        className="flex gap-1 overflow-x-auto border-b border-line"
      >
        {tabs.map((option) => (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={tab === option.id}
            onClick={() => setTab(option.id)}
            className={`-mb-px min-h-12 cursor-pointer whitespace-nowrap border-0 border-b-2 bg-transparent px-4 py-3 text-[15px] ${
              tab === option.id
                ? "border-ink font-semibold text-ink"
                : "border-transparent font-medium text-ink-soft"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {!isLoaded && !loadFailed ? (
        <div
          aria-busy="true"
          aria-label="Loading memories"
          className="flex flex-col gap-5"
        >
          <span className="block h-[18px] w-[140px] rounded bg-subtle" />
          <span className="block h-[140px] rounded-card bg-subtle" />
          <span className="block h-[18px] w-[120px] rounded bg-subtle" />
          <span className="block h-[100px] rounded-card bg-subtle" />
        </div>
      ) : null}

      {loadFailed ? (
        <LoadFailed
          title="We couldn’t load your memories"
          body="Something went wrong on our side. Nothing has been deleted."
          onRetry={() => {
            for (const query of queries) {
              void query.refetch();
            }
          }}
        />
      ) : null}

      {isLoaded && groups && tab === "memories" ? (
        <MemoryItemsList groups={groups} timeZone={timeZone} />
      ) : null}

      {isLoaded && summaries && tab === "summaries" ? (
        <ConversationSummariesList summaries={summaries} timeZone={timeZone} />
      ) : null}

      {isLoaded && photos && tab === "photos" ? (
        <SharedPhotosList photos={photos} timeZone={timeZone} />
      ) : null}
    </>
  );
}
