"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { EmptyState } from "@/components/EmptyState";
import { FilterPills } from "@/components/FilterPills";
import { LoadFailed } from "@/components/LoadFailed";
import { UnmatchedEntryCard } from "@/components/UnmatchedEntryCard";
import type { UnmatchedEntry } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import {
  FILTER_OPTIONS,
  type UnmatchedFilter,
  type UnmatchedMarkDraft,
} from "@/lib/unmatched-entry-draft";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Unmatched Patterns review, from the card-list template with
 * the table template's filter pills: a folding card per entry to set its
 * mark. It starts on the entries still to review. Entries are general
 * descriptions with a count of Users, never a User's own words.
 *
 * @returns The pills and the list, or a loading, empty or error state.
 */
export function UnmatchedPatternsManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<UnmatchedFilter>("to_review");
  const [flash, setFlash] = useState<Flash | null>(null);
  const mark = filter === "all" ? null : filter;

  const listQuery = useQuery({
    queryKey: queryKeys.unmatchedEntries(mark),
    queryFn: () => apiClient.listUnmatchedEntries(mark),
  });
  const list = listQuery.data;

  async function save(entry: UnmatchedEntry, draft: UnmatchedMarkDraft) {
    await apiClient.markUnmatchedEntry(
      entry.id,
      draft.mark,
      draft.mark === "folded" ? draft.patternTypeId : null,
    );
    setFlash({ text: "Saved the mark.", isError: false });
    await queryClient.invalidateQueries({
      queryKey: queryKeys.everyUnmatchedEntries,
    });
  }

  const pills = (
    <FilterPills
      label="Mark"
      options={FILTER_OPTIONS}
      chosen={filter}
      onChoose={(chosen) => {
        setFilter(chosen);
        setFlash(null);
      }}
    />
  );

  if (!list) {
    return (
      <>
        {pills}
        {listQuery.isError ? (
          <LoadFailed
            title="Couldn’t load the unmatched entries"
            body="Nothing was changed."
            onRetry={() => void listQuery.refetch()}
          />
        ) : (
          <CardListLoading label="Loading the unmatched entries" />
        )}
      </>
    );
  }

  return (
    <>
      {pills}
      <CardList
        key={filter}
        items={list.entries}
        count={
          <CardCount
            count={list.entries.length}
            words={list.entries.length === 1 ? "entry" : "entries"}
          />
        }
        aboveList={
          <>
            <CardListFlash flash={flash} />
            {list.entries.length === 0 ? (
              <EmptyState
                title={
                  filter === "to_review"
                    ? "Nothing to review"
                    : "No entries here"
                }
                body="When Zeph keeps noticing something that fits no Pattern Type, it shows up here as a general description, after a Conversation ends."
              />
            ) : null}
          </>
        }
        renderCard={(entry, _index, folding) => (
          <UnmatchedEntryCard
            key={entry.id}
            entry={entry}
            patternTypes={list.pattern_types}
            isOpen={folding.isOpen}
            onToggle={folding.onToggle}
            onSave={(draft) => save(entry, draft)}
          />
        )}
      />
    </>
  );
}
