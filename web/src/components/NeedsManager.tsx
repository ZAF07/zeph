"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { LoadFailed } from "@/components/LoadFailed";
import { NeedCard } from "@/components/NeedCard";
import { NewNeedBox } from "@/components/NewNeedBox";
import type { MoveDirection, Need, NeedInput } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Needs manager, from the card-list template: a folding card per
 * Need, in order, to edit, move or remove it and pick the Moves it rules
 * out, and a box above the list to add one. The fallback Need can't be
 * removed.
 *
 * @returns The list, or a loading or error state.
 */
export function NeedsManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);
  const needsQuery = useQuery({
    queryKey: queryKeys.needs,
    queryFn: () => apiClient.listNeeds(),
  });
  const movesQuery = useQuery({
    queryKey: queryKeys.moves,
    queryFn: () => apiClient.listMoves(),
  });
  const moveMutation = useMutation({
    mutationFn: ({
      need,
      direction,
    }: {
      need: Need;
      direction: MoveDirection;
    }) => apiClient.moveNeed(need.id, direction),
    onMutate: () => setFlash(null),
    onSuccess: (needs) => queryClient.setQueryData(queryKeys.needs, needs),
    onError: (_, { need }) =>
      setFlash({
        text: `Couldn’t move ${need.name}. Please try again.`,
        isError: true,
      }),
  });
  const needs = needsQuery.data;
  const moves = movesQuery.data;

  async function reloadNeeds() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.needs });
  }

  async function add(input: NeedInput) {
    await apiClient.addNeed(input);
    setIsAdding(false);
    setFlash({ text: `Added ${input.name.trim()}.`, isError: false });
    await reloadNeeds();
  }

  async function save(need: Need, input: NeedInput) {
    await apiClient.updateNeed(need.id, input);
    setFlash({ text: `Saved ${input.name.trim()}.`, isError: false });
    await reloadNeeds();
  }

  async function remove(need: Need) {
    await apiClient.deleteNeed(need.id);
    setFlash({ text: `Removed ${need.name}.`, isError: false });
    await reloadNeeds();
  }

  if (!needs || !moves) {
    if (needsQuery.isError || movesQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Needs"
          body="Zeph keeps using the last saved Needs."
          onRetry={() => {
            void needsQuery.refetch();
            void movesQuery.refetch();
          }}
        />
      );
    }
    return <CardListLoading label="Loading Needs" />;
  }

  return (
    <CardList
      items={needs}
      count={
        <CardCount
          count={needs.length}
          words={needs.length === 1 ? "Need" : "Needs"}
        />
      }
      addLabel="Add Need"
      onAdd={() => {
        setIsAdding(true);
        setFlash(null);
      }}
      isAddDisabled={isAdding}
      aboveList={
        <>
          <CardListFlash flash={flash} />
          {isAdding ? (
            <NewNeedBox
              moves={moves}
              onAdd={add}
              onCancel={() => setIsAdding(false)}
            />
          ) : null}
        </>
      }
      renderCard={(need, index, folding) => (
        <NeedCard
          key={need.id}
          need={need}
          moves={moves}
          isOpen={folding.isOpen}
          onToggle={folding.onToggle}
          onSave={(input) => save(need, input)}
          onRemove={() => remove(need)}
          onMove={(direction) => moveMutation.mutate({ need, direction })}
          canMoveUp={index > 0}
          canMoveDown={index < needs.length - 1}
          isMoving={moveMutation.isPending}
        />
      )}
    />
  );
}
