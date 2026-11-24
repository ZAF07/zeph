"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ArchivedThoughtExperimentCard } from "@/components/ArchivedThoughtExperimentCard";
import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { NewThoughtExperimentBox } from "@/components/NewThoughtExperimentBox";
import { ThoughtExperimentCard } from "@/components/ThoughtExperimentCard";
import type {
  ThoughtExperiment,
  ThoughtExperimentInput,
} from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Thought Experiments manager, from the card-list template: a
 * folding card per Thought Experiment to change it, switch it off or
 * archive it; then the archived ones, read only; and a box above the list
 * to add one. There is no delete.
 *
 * @returns The lists, or a loading, empty or error state.
 */
export function ThoughtExperimentsManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);

  const listQuery = useQuery({
    queryKey: queryKeys.thoughtExperiments,
    queryFn: () => apiClient.listThoughtExperiments(),
  });
  const list = listQuery.data;

  async function reload() {
    await queryClient.invalidateQueries({
      queryKey: queryKeys.thoughtExperiments,
    });
  }

  async function add(input: ThoughtExperimentInput, saveAnyway: boolean) {
    await apiClient.addThoughtExperiment(input, saveAnyway);
    setIsAdding(false);
    setFlash({ text: "Added the Thought Experiment.", isError: false });
    await reload();
  }

  async function save(
    thoughtExperiment: ThoughtExperiment,
    input: ThoughtExperimentInput,
    saveAnyway: boolean,
  ) {
    await apiClient.updateThoughtExperiment(
      thoughtExperiment.id,
      input,
      saveAnyway,
    );
    setFlash({ text: "Saved the Thought Experiment.", isError: false });
    await reload();
  }

  async function archive(thoughtExperiment: ThoughtExperiment) {
    await apiClient.archiveThoughtExperiment(thoughtExperiment.id);
    setFlash({
      text: "Archived the Thought Experiment. Past tries still show it.",
      isError: false,
    });
    await reload();
  }

  if (!list) {
    if (listQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Thought Experiments"
          body="Zeph keeps using the last saved set."
          onRetry={() => void listQuery.refetch()}
        />
      );
    }
    return <CardListLoading label="Loading Thought Experiments" />;
  }

  const current = list.thought_experiments.filter(
    (thoughtExperiment) => thoughtExperiment.archived_at === null,
  );
  const archived = list.thought_experiments.filter(
    (thoughtExperiment) => thoughtExperiment.archived_at !== null,
  );

  return (
    <>
      <CardList
        items={current}
        count={
          <CardCount
            count={current.length}
            words={
              current.length === 1
                ? "Thought Experiment"
                : "Thought Experiments"
            }
          />
        }
        addLabel="Add a Thought Experiment"
        onAdd={() => {
          setIsAdding(true);
          setFlash(null);
        }}
        isAddDisabled={isAdding}
        aboveList={
          <>
            <CardListFlash flash={flash} />
            {isAdding ? (
              <NewThoughtExperimentBox
                patternTypes={list.pattern_types}
                onAdd={add}
                onCancel={() => setIsAdding(false)}
              />
            ) : null}
            {current.length === 0 && !isAdding ? (
              <EmptyState
                title="No Thought Experiments"
                body="Without one, Zeph tells look-alike Patterns apart only from the stories Users tell. Add one to begin."
              />
            ) : null}
          </>
        }
        renderCard={(thoughtExperiment, _index, folding) => (
          <ThoughtExperimentCard
            key={thoughtExperiment.id}
            thoughtExperiment={thoughtExperiment}
            patternTypes={list.pattern_types}
            isOpen={folding.isOpen}
            onToggle={folding.onToggle}
            onSave={(input, saveAnyway) =>
              save(thoughtExperiment, input, saveAnyway)
            }
            onArchive={() => archive(thoughtExperiment)}
          />
        )}
      />
      {archived.length > 0 ? (
        <CardList
          items={archived}
          count={<CardCount count={archived.length} words="archived" />}
          startsFolded
          renderCard={(thoughtExperiment, _index, folding) => (
            <ArchivedThoughtExperimentCard
              key={thoughtExperiment.id}
              thoughtExperiment={thoughtExperiment}
              isOpen={folding.isOpen}
              onToggle={folding.onToggle}
            />
          )}
        />
      ) : null}
    </>
  );
}
