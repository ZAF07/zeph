"use client";

import { useCallback, useEffect, useState } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { ConversationSummariesList } from "@/components/ConversationSummariesList";
import { LoadFailed } from "@/components/LoadFailed";
import { MemoryNote } from "@/components/MemoryNote";
import { MemoryItemsList } from "@/components/MemoryItemsList";
import { SharedPhotosList } from "@/components/SharedPhotosList";
import { Switch } from "@/components/Switch";
import type {
  ConversationSummary,
  Me,
  MemoryGroup,
  SharedPhoto,
} from "@/lib/api-client";
import { notAvailableText } from "@/lib/features";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | {
      kind: "loaded";
      me: Me;
      groups: MemoryGroup[];
      summaries: ConversationSummary[];
      photos: SharedPhoto[];
    };

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
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [tab, setTab] = useState<Tab>("memories");
  const [isSavingSwitch, setIsSavingSwitch] = useState(false);
  const [switchFailed, setSwitchFailed] = useState(false);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const [me, groups, summaries, photos] = await Promise.all([
        apiClient.getMe(),
        apiClient.listMemoryGroups(),
        apiClient.listConversationSummaries(),
        apiClient.listSharedPhotos(),
      ]);
      setState({ kind: "loaded", me, groups, summaries, photos });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  async function saveUserMemorySetting(enabled: boolean) {
    setIsSavingSwitch(true);
    setSwitchFailed(false);
    try {
      const me = await apiClient.updatePreferences({
        user_memory_enabled: enabled,
      });
      setState((current) =>
        current.kind === "loaded" ? { ...current, me } : current,
      );
    } catch {
      setSwitchFailed(true);
    } finally {
      setIsSavingSwitch(false);
    }
  }

  const memoryOn = state.kind === "loaded" && state.me.user_memory_enabled;
  const memoryUnavailable =
    state.kind === "loaded" && !state.me.user_memory_available;
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
        {state.kind === "loaded" ? (
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-3 rounded-full border border-line bg-white py-1.5 pr-1.5 pl-[18px]">
              <span className="text-sm font-medium">{switchLabel}</span>
              <Switch
                label="Memory"
                checked={memoryOn}
                disabled={isSavingSwitch || memoryUnavailable}
                onChange={(next) => void saveUserMemorySetting(next)}
              />
            </div>
            <ChangedInChatCaption
              changedAt={state.me.changed_in_chat.user_memory}
              timeZone={state.me.time_zone ?? undefined}
            />
            {switchFailed ? (
              <p role="alert" className="m-0 text-sm text-danger-deep">
                We couldn’t change that. Please try again.
              </p>
            ) : null}
          </div>
        ) : null}
      </header>

      {state.kind === "loaded" ? (
        <MemoryNote note={state.me.memory_note} />
      ) : null}

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

      {state.kind === "loading" ? (
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

      {state.kind === "failed" ? (
        <LoadFailed
          title="We couldn’t load your memories"
          body="Something went wrong on our side. Nothing has been deleted."
          onRetry={() => void load()}
        />
      ) : null}

      {state.kind === "loaded" && tab === "memories" ? (
        <MemoryItemsList
          groups={state.groups}
          timeZone={state.me.time_zone ?? undefined}
          onGroupsChange={(groups) =>
            setState((current) =>
              current.kind === "loaded" ? { ...current, groups } : current,
            )
          }
        />
      ) : null}

      {state.kind === "loaded" && tab === "summaries" ? (
        <ConversationSummariesList
          summaries={state.summaries}
          timeZone={state.me.time_zone ?? undefined}
          onSummariesChange={(summaries) =>
            setState((current) =>
              current.kind === "loaded" ? { ...current, summaries } : current,
            )
          }
        />
      ) : null}

      {state.kind === "loaded" && tab === "photos" ? (
        <SharedPhotosList
          photos={state.photos}
          timeZone={state.me.time_zone ?? undefined}
          onPhotosChange={(photos) =>
            setState((current) =>
              current.kind === "loaded" ? { ...current, photos } : current,
            )
          }
        />
      ) : null}
    </>
  );
}
